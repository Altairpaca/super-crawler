"""文本清洗工具"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """清洗文本：去除多余空白、HTML标签等"""
    if not text:
        return ""
    # 去HTML标签
    text = re.sub(r"<[^>]+>", "", text)
    # 去多余空白
    text = re.sub(r"\s+", " ", text)
    # 去首尾空白
    return text.strip()


def truncate(text: str, max_len: int = 500, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def extract_tags(text: str, candidates: list[str] | None = None) -> list[str]:
    """从文本中提取标签/关键词"""
    if not text:
        return []
    if candidates:
        text_lower = text.lower()
        return [t for t in candidates if t.lower() in text_lower]
    # 简单的关键词提取：大写词和#标签
    hashtags = re.findall(r"#(\w+)", text)
    return list(set(hashtags))[:10]
