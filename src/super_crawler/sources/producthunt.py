"""ProductHunt数据源 — 官方API v2"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry

PH_API = "https://api.producthunt.com/v2/api/graphql"


class ProductHuntSource(CrawlerSource):
    """ProductHunt爬虫。

    使用官方GraphQL API（无需token可获取每日榜单）。
    如果有token，可获取更多数据。
    """

    name = "producthunt"
    description = "ProductHunt新产品发现"

    def __init__(self, config: CrawlerConfig | None = None):
        super().__init__(config)
        self._token = self.config.firecrawl_api_key  # 复用 env

    @retry(max_attempts=2, delay=2)
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索ProductHunt"""
        # PH没有公开搜索API，用Firecrawl fallback
        from .web_generic import WebGenericSource
        web = WebGenericSource(self.config)
        results = web.search(f"site:producthunt.com {query}", limit)
        # 标记来源
        for r in results:
            r.source = "producthunt"
        return results

    def trending(self, limit: int = 20) -> list[CrawlResult]:
        """获取今日/近日热门产品"""
        today = datetime.now().strftime("%Y-%m-%d")
        query = """
        {
          posts(order: VOTES, postedAfter: "%sT00:00:00Z") {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
                commentsCount
                createdAt
                topics { edges { node { name } } }
                website
              }
            }
          }
        }
        """ % today

        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        payload = json.dumps({"query": query}).encode()
        req = urllib.request.Request(PH_API, data=payload, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                edges = data.get("data", {}).get("posts", {}).get("edges", [])
        except Exception:
            # API失败，用Firecrawl抓首页
            return self._fallback_trending(limit)

        results = []
        for edge in edges[:limit]:
            node = edge.get("node", {})
            topics = [
                t["node"]["name"]
                for t in node.get("topics", {}).get("edges", [])
            ]
            results.append(CrawlResult(
                title=node.get("name", ""),
                url=node.get("url", ""),
                source="producthunt",
                content=node.get("tagline", ""),
                tags=topics,
                metrics={
                    "votes": node.get("votesCount", 0),
                    "comments": node.get("commentsCount", 0),
                },
                published=node.get("createdAt", ""),
                raw={
                    "website": node.get("website", ""),
                    "ph_id": node.get("id", ""),
                },
            ))
        return results

    def _fallback_trending(self, limit: int) -> list[CrawlResult]:
        """Firecrawl fallback"""
        from .web_generic import WebGenericSource
        web = WebGenericSource(self.config)
        results = web.search("site:producthunt.com AI tools today", limit)
        for r in results:
            r.source = "producthunt"
        return results
