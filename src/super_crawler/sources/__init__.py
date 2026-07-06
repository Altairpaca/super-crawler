"""数据源模块"""

from .github import GitHubSource
from .arxiv import ArxivSource
from .web_generic import WebGenericSource
from .producthunt import ProductHuntSource
from .hackernews import HackerNewsSource

# 可选依赖的源
try:
    from .semantic_scholar import SemanticScholarSource
except ImportError:
    SemanticScholarSource = None  # type: ignore

ALL_SOURCES = {
    "github": GitHubSource,
    "arxiv": ArxivSource,
    "web": WebGenericSource,
    "producthunt": ProductHuntSource,
    "hackernews": HackerNewsSource,
}

if SemanticScholarSource is not None:
    ALL_SOURCES["semantic_scholar"] = SemanticScholarSource

__all__ = list(ALL_SOURCES.keys())
