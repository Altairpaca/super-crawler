"""HackerNews数据源 — Algolia API（无需认证）"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from datetime import datetime

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry
from ..utils.text import clean_text, truncate

HN_SEARCH = "https://hn.algolia.com/api/v1/search"
HN_TOP = "https://hn.algolia.com/api/v1/search?tags=front_page"


class HackerNewsSource(CrawlerSource):
    """HackerNews爬虫 — 使用Algolia公开API，无需认证。"""

    name = "hackernews"
    description = "HackerNews讨论 + AI/tech趋势"

    @retry(max_attempts=2, delay=1)
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索HN"""
        params = urllib.parse.urlencode({
            "query": query,
            "tags": "story",
            "hitsPerPage": limit,
        })
        url = f"{HN_SEARCH}?{params}"
        items = self._fetch(url)
        return [self._item_to_result(item) for item in items[:limit]]

    def trending(self, limit: int = 20) -> list[CrawlResult]:
        """获取HN首页热门"""
        items = self._fetch(f"{HN_TOP}&hitsPerPage={limit}")
        return [self._item_to_result(item) for item in items[:limit]]

    def recent_ai(self, limit: int = 20) -> list[CrawlResult]:
        """最近24小时AI相关帖子"""
        params = urllib.parse.urlencode({
            "query": "AI agent LLM GPT",
            "tags": "story",
            "hitsPerPage": limit,
            "numericFilters": f"created_at_i>{int(datetime.now().timestamp()) - 86400}",
        })
        url = f"{HN_SEARCH}?{params}"
        items = self._fetch(url)
        return [self._item_to_result(item) for item in items[:limit]]

    def _fetch(self, url: str) -> list[dict]:
        req = urllib.request.Request(
            url, headers={"User-Agent": self.config.user_agent}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                return data.get("hits", [])
        except Exception:
            return []

    def _item_to_result(self, item: dict) -> CrawlResult:
        title = item.get("title", "")
        hn_id = item.get("objectID", "")
        url = item.get("url") or f"https://news.ycombinator.com/item?id={hn_id}"
        return CrawlResult(
            title=title,
            url=url,
            source="hackernews",
            content=truncate(clean_text(item.get("story_text", "") or ""), 1000),
            tags=[],
            metrics={
                "points": item.get("points", 0),
                "comments": item.get("num_comments", 0),
            },
            authors=[item.get("author", "")],
            published=item.get("created_at", ""),
            raw={
                "hn_id": hn_id,
                "hn_url": f"https://news.ycombinator.com/item?id={hn_id}",
            },
        )
