"""统一接口 + 数据模型"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class CrawlResult:
    """所有数据源返回的统一数据结构"""

    title: str
    url: str
    source: str  # "github" / "arxiv" / "producthunt" / ...
    content: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    authors: list[str] = field(default_factory=list)
    published: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """基于URL的去重哈希"""
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["discovered_at"] = self.discovered_at.isoformat()
        return d


class CrawlerSource(ABC):
    """所有数据源的基类。

    子类必须实现 search() 和 trending()。
    extract() 为可选实现。
    """

    name: str = "base"
    description: str = ""

    def __init__(self, config: "CrawlerConfig | None" = None):
        from .config import default_config
        self.config = config or default_config()

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索：根据关键词返回条目列表"""

    @abstractmethod
    def trending(self, limit: int = 20) -> list[CrawlResult]:
        """趋势：获取当前热门/最新条目"""

    def extract(self, url: str) -> CrawlResult | None:
        """提取：抓取单个URL的完整内容（可选实现）"""
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
