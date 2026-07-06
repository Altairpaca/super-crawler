"""LLM内容草稿生成"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..storage.sqlite_store import SqliteStore


def generate_daily_digest(
    store: SqliteStore,
    max_items: int = 10,
    language: str = "zh",
) -> str:
    """从最近采集的数据生成每日速报草稿。

    返回纯文本草稿，由人工润色后发布。
    """
    recent = store.recent(limit=max_items * 3)  # 多取一些，筛选

    if not recent:
        return "暂无新数据，跳过今日速报。"

    # 按source分组
    by_source: dict[str, list] = {}
    for item in recent:
        src = item["source"]
        by_source.setdefault(src, []).append(item)

    now = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# AI工具速报 — {now}\n"]

    source_labels = {
        "github": "🔧 GitHub热门项目",
        "producthunt": "🚀 ProductHunt新品",
        "hackernews": "💬 HackerNews热议",
        "arxiv": "📄 arXiv论文",
        "semantic_scholar": "📚 学术论文",
        "web": "🌐 网页内容",
    }

    for source, label in source_labels.items():
        items = by_source.get(source, [])[:5]
        if not items:
            continue
        lines.append(f"\n## {label}\n")
        for item in items:
            title = item.get("title", "无标题")
            url = item.get("url", "")
            content = (item.get("content") or "")[:150]
            metrics = json.loads(item.get("metrics") or "{}")

            metrics_str = ""
            if metrics.get("stars"):
                metrics_str += f" ⭐{metrics['stars']}"
            if metrics.get("votes"):
                metrics_str += f" 👍{metrics['votes']}"
            if metrics.get("points"):
                metrics_str += f" 📊{metrics['points']}"

            lines.append(f"- **[{title}]({url})**{metrics_str}")
            if content:
                lines.append(f"  > {content}\n")

    lines.append(f"\n---\n*自动生成于 {now}，需人工润色后发布*")
    return "\n".join(lines)


def generate_topic_suggestions(store: SqliteStore) -> str:
    """基于近期数据生成选题建议"""
    recent = store.recent(limit=50)
    if not recent:
        return "数据不足，无法生成选题建议。"

    # 统计标签频率
    tag_count: dict[str, int] = {}
    for item in recent:
        tags = json.loads(item.get("tags") or "[]")
        for tag in tags:
            tag_count[tag] = tag_count.get(tag, 0) + 1

    # 热门标签
    top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:15]

    lines = ["# 选题建议\n"]
    lines.append("## 热门标签（近期出现频率）\n")
    for tag, count in top_tags:
        lines.append(f"- `{tag}` × {count}")

    lines.append("\n## 可能的选题方向\n")
    if top_tags:
        lines.append(f"1. 围绕 `{top_tags[0][0]}` 写深度解析")
        lines.append(f"2. `{top_tags[0][0]}` vs `{top_tags[1][0]}` 对比评测")
        lines.append(f"3. 本周 `{top_tags[0][0]}` 生态变化总结")

    return "\n".join(lines)
