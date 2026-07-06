"""arXiv数据源 — 官方API"""

from __future__ import annotations

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry

ARXIV_API = "http://export.arxiv.org/api/query"

AI_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.RO",
    "cs.IR", "cs.SE", "stat.ML", "cs.MA", "cs.NE",
]

_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivSource(CrawlerSource):
    """arXiv论文爬虫"""

    name = "arxiv"
    description = "arXiv学术论文搜索"

    @retry(max_attempts=2, delay=2)
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索arXiv论文"""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        return self._fetch(params)

    def trending(self, category: str = "cs.AI", limit: int = 20) -> list[CrawlResult]:  # type: ignore[override]
        """获取某分类最新论文"""
        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        return self._fetch(params)

    def search_ai(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索AI领域论文（限定分类）"""
        cat_query = " OR ".join(f"cat:{c}" for c in AI_CATEGORIES[:5])
        params = {
            "search_query": f"all:{query} AND ({cat_query})",
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        return self._fetch(params)

    def _fetch(self, params: dict) -> list[CrawlResult]:
        url = ARXIV_API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"User-Agent": self.config.user_agent}
        )
        try:
            # arXiv API走直连，不走代理（Clash会导致502）
            saved = {}
            for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
                saved[k] = os.environ.pop(k, None)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    xml_data = resp.read().decode("utf-8")
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
        except Exception:
            return []

        results = []
        try:
            root = ET.fromstring(xml_data)
            for entry in root.findall("atom:entry", _NS):
                arxiv_id = entry.find("atom:id", _NS).text.split("/")[-1]
                title = entry.find("atom:title", _NS).text.strip().replace("\n", " ")
                abstract = entry.find("atom:summary", _NS).text.strip().replace("\n", " ")
                published = entry.find("atom:published", _NS).text[:10]
                authors = [
                    a.find("atom:name", _NS).text
                    for a in entry.findall("atom:author", _NS)
                ]
                categories = [
                    c.get("term") for c in entry.findall("atom:category", _NS)
                ]
                pdf_url = ""
                for link in entry.findall("atom:link", _NS):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")

                results.append(CrawlResult(
                    title=title,
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    source="arxiv",
                    content=abstract,
                    authors=authors,
                    tags=categories,
                    published=published,
                    raw={"arxiv_id": arxiv_id, "pdf_url": pdf_url},
                ))
        except ET.ParseError:
            pass

        return results
