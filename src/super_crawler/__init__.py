"""Super Crawler — 可复用的多源数据采集框架"""

__version__ = "0.1.0"

from .base import CrawlerSource, CrawlResult
from .config import CrawlerConfig

__all__ = ["CrawlerSource", "CrawlResult", "CrawlerConfig"]
