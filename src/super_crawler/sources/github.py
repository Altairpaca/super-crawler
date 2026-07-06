"""GitHub数据源 — gh CLI + REST API"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

from ..base import CrawlerSource, CrawlResult
from ..config import CrawlerConfig
from ..utils.retry import retry


class GitHubSource(CrawlerSource):
    """GitHub爬虫：搜索仓库、趋势、用户仓库。

    优先用gh CLI，fallback到REST API。
    """

    name = "github"
    description = "GitHub仓库搜索、趋势、用户仓库"

    def __init__(self, config: CrawlerConfig | None = None):
        super().__init__(config)
        self.config.apply_proxies()
        # 找gh CLI
        self._gh_bin = self._find_gh()

    def _find_gh(self) -> str | None:
        """查找gh CLI路径"""
        for path in [
            "/home/altair/miniforge3/envs/crawlers/bin/gh",
            "/usr/bin/gh",
            "gh",
        ]:
            try:
                result = subprocess.run(
                    [path, "--version"], capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def _gh_cmd(self, args: list[str], timeout: int = 30) -> str:
        """执行gh命令"""
        if not self._gh_bin:
            return ""
        cmd = [self._gh_bin] + args + ["--json"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout
        except Exception:
            return ""

    def _api_search(self, query: str, limit: int = 20, sort: str = "stars") -> list[dict]:
        """REST API fallback"""
        url = (
            f"https://api.github.com/search/repositories?"
            f"q={urllib.parse.quote(query)}&sort={sort}&per_page={limit}"
        )
        headers = {"User-Agent": self.config.user_agent, "Accept": "application/vnd.github.v3+json"}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                return data.get("items", [])
        except Exception:
            return []

    @retry(max_attempts=2, delay=1)
    def search(self, query: str, limit: int = 10) -> list[CrawlResult]:
        """搜索GitHub仓库"""
        # 先尝试gh CLI
        raw = self._gh_cmd(["api", f"search/repositories?q={query}&sort=stars&per_page={limit}"])
        if raw:
            try:
                items = json.loads(raw).get("items", [])
            except json.JSONDecodeError:
                items = []
        else:
            items = self._api_search(query, limit)

        return [self._item_to_result(item) for item in items[:limit]]

    def trending(self, language: str = "", limit: int = 20) -> list[CrawlResult]:  # type: ignore[override]
        """获取GitHub趋势（通过搜索最近创建的高星项目模拟）"""
        since = datetime.now().strftime("%Y-%m-01")
        query = f"stars:>50 created:>{since}"
        if language:
            query += f" language:{language}"
        return self.search(query, limit)

    def user_repos(self, username: str, limit: int = 20) -> list[CrawlResult]:
        """获取用户仓库"""
        raw = self._gh_cmd(["api", f"users/{username}/repos?sort=stars&per_page={limit}"])
        if not raw:
            return []
        try:
            items = json.loads(raw)
            if isinstance(items, dict):
                items = items.get("items", [])
        except json.JSONDecodeError:
            items = []
        return [self._item_to_result(item) for item in items[:limit]]

    def _item_to_result(self, item: dict) -> CrawlResult:
        return CrawlResult(
            title=item.get("full_name", ""),
            url=item.get("html_url", ""),
            source="github",
            content=item.get("description", "") or "",
            tags=item.get("topics", []),
            metrics={
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
            },
            published=item.get("created_at", ""),
            raw={
                "language": item.get("language", ""),
                "license": (item.get("license") or {}).get("spdx_id", ""),
            },
        )
