"""SemanticScholar数据源 — 引用网络分析（可选依赖）"""

from __future__ import annotations

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry

try:
    from semanticscholar import SemanticScholar
    HAS_S2 = True
except ImportError:
    HAS_S2 = False


class SemanticScholarSource(CrawlerSource):
    """SemanticScholar论文爬虫（需安装 semanticscholar 包）"""

    name = "semantic_scholar"
    description = "SemanticScholar论文搜索 + 引用网络"

    def __init__(self, config: CrawlerConfig | None = None):
        super().__init__(config)
        if not HAS_S2:
            raise ImportError(
                "需要安装 semanticscholar: pip install semanticscholar"
            )
        self._sch = SemanticScholar(api_key=self.config.semantic_scholar_api_key or None)

    @retry(max_attempts=2, delay=2)
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        fields = [
            "title", "abstract", "authors", "year", "citationCount",
            "referenceCount", "venue", "publicationDate", "externalIds",
            "openAccessPdf",
        ]
        results = self._sch.search_paper(query, limit=limit, fields=fields)
        return [
            CrawlResult(
                title=p.title or "",
                url=f"https://www.semanticscholar.org/paper/{p.paperId}",
                source="semantic_scholar",
                content=(p.abstract or "")[:500],
                authors=[a.name for a in (p.authors or [])[:5]],
                tags=[],
                metrics={
                    "citations": p.citationCount or 0,
                    "references": p.referenceCount or 0,
                },
                published=str(p.year or ""),
                raw={
                    "paperId": p.paperId,
                    "venue": p.venue or "",
                    "doi": (p.externalIds or {}).get("DOI", ""),
                    "arxiv_id": (p.externalIds or {}).get("ArXiv", ""),
                    "pdf_url": (p.openAccessPdf or {}).get("url", "") if p.openAccessPdf else "",
                },
            )
            for p in results.items
        ]

    def trending(self, limit: int = 20) -> list[CrawlResult]:
        """SemanticScholar不直接支持趋势，用最近高引论文模拟"""
        return self.search("AI agent 2026", limit)

    def paper_details(self, paper_id: str) -> dict | None:
        """获取论文详情 + 引用"""
        paper = self._sch.get_paper(paper_id, fields=[
            "title", "abstract", "year", "citationCount",
            "citations.title", "citations.citationCount",
            "tldr",
        ])
        if not paper:
            return None
        return {
            "title": paper.title,
            "abstract": paper.abstract,
            "year": paper.year,
            "citations": paper.citationCount,
            "tldr": paper.tldr.text if paper.tldr else "",
            "top_citations": [
                {"title": c.title, "citations": c.citationCount}
                for c in (paper.citations or [])[:10]
            ],
        }
