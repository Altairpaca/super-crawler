"""配置管理 — 代理/DB路径/Firecrawl等"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class CrawlerConfig:
    """爬虫全局配置"""

    # 数据库路径 — 各profile可以指向不同的DB
    db_path: Path = field(default_factory=lambda: Path("data/crawlers.db"))

    # 代理
    http_proxy: str = "http://127.0.0.1:7890"
    https_proxy: str = "http://127.0.0.1:7890"

    # Firecrawl
    firecrawl_url: str = "http://localhost:3002"
    firecrawl_api_key: str = ""

    # GitHub
    github_token: str = ""

    # SemanticScholar
    semantic_scholar_api_key: str = ""

    # 速率限制 (请求/分钟)
    rate_limit: int = 30

    # User-Agent
    user_agent: str = "SuperCrawler/0.1 (research agent)"

    def apply_proxies(self) -> None:
        """设置环境变量代理"""
        if self.http_proxy:
            os.environ["HTTP_PROXY"] = self.http_proxy
        if self.https_proxy:
            os.environ["HTTPS_PROXY"] = self.https_proxy

    def ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


def default_config() -> CrawlerConfig:
    """从环境变量 + .env 文件加载默认配置"""
    # 尝试加载 .env
    for env_path in [
        Path.cwd() / ".env",
        Path.home() / ".env",
        Path.home() / "repos" / "super-crawler" / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            break

    return CrawlerConfig(
        db_path=Path(os.environ.get("CRAWLER_DB_PATH", "data/crawlers.db")),
        http_proxy=os.environ.get("HTTP_PROXY", "http://127.0.0.1:7890"),
        https_proxy=os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7890"),
        firecrawl_url=os.environ.get("FIRECRAWL_URL", "http://localhost:3002"),
        firecrawl_api_key=os.environ.get("FIRECRAWL_API_KEY", ""),
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY", ""),
    )
