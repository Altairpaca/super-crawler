"""通用网页爬虫 — Firecrawl + httpx fallback"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry
from ..utils.text import clean_text, truncate


class WebGenericSource(CrawlerSource):
    """通用网页爬虫。

    优先Firecrawl（自部署），fallback到httpx。
    """

    name = "web"
    description = "通用网页抓取 + 搜索"

    @retry(max_attempts=2, delay=1)
    def search(self, query: str, limit: int = 5) -> list[CrawlResult]:
        """通过Firecrawl搜索"""
        results = self._firecrawl_search(query, limit)
        return [
            CrawlResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                source="web",
                content=truncate(clean_text(r.get("markdown", "") or r.get("description", "")), 2000),
                tags=[],
            )
            for r in results if r.get("url")
        ]

    def trending(self, limit: int = 20) -> list[CrawlResult]:
        """Web没有原生趋势，返回空"""
        return []

    @retry(max_attempts=2, delay=1)
    def extract(self, url: str) -> CrawlResult | None:
        """通过Firecrawl抓取单个URL"""
        data = self._firecrawl_scrape(url)
        if not data:
            return None
        return CrawlResult(
            title=data.get("metadata", {}).get("title", url),
            url=url,
            source="web",
            content=truncate(clean_text(data.get("markdown", "")), 5000),
        )

    def _firecrawl_search(self, query: str, limit: int = 5) -> list[dict]:
        payload = json.dumps({"query": query, "limit": limit}).encode()
        req = urllib.request.Request(
            f"{self.config.firecrawl_url}/v1/search",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                if result.get("success"):
                    return result.get("data", [])
        except Exception:
            pass
        return []

    def _firecrawl_scrape(self, url: str) -> dict | None:
        payload = json.dumps({"url": url, "formats": ["markdown"]}).encode()
        req = urllib.request.Request(
            f"{self.config.firecrawl_url}/v1/scrape",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                if result.get("success"):
                    return result.get("data")
        except Exception:
            pass
        return None
