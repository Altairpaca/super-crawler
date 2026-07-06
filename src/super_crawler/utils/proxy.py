"""代理自动配置"""

from __future__ import annotations

import os


def ensure_proxy(
    http: str = "http://127.0.0.1:7890",
    https: str = "http://127.0.0.1:7890",
    force: bool = False,
) -> None:
    """确保代理环境变量已设置。

    默认不覆盖已有的值，force=True 时强制覆盖。
    """
    if force or not os.environ.get("HTTP_PROXY"):
        os.environ["HTTP_PROXY"] = http
    if force or not os.environ.get("HTTPS_PROXY"):
        os.environ["HTTPS_PROXY"] = https


def proxy_status() -> dict[str, str]:
    """返回当前代理状态"""
    return {
        "HTTP_PROXY": os.environ.get("HTTP_PROXY", "(未设置)"),
        "HTTPS_PROXY": os.environ.get("HTTPS_PROXY", "(未设置)"),
    }
