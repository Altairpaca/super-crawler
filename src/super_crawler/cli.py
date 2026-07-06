"""Super Crawler CLI — 统一命令行入口"""

from __future__ import annotations

import sys
import json
import time
from pathlib import Path

from .config import CrawlerConfig, default_config
from .storage.sqlite_store import SqliteStore
from .generators.draft import generate_daily_digest, generate_topic_suggestions


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__ or _HELP)
        return

    cmd = args[0]
    rest = args[1:]

    config = default_config()

    # --db 参数覆盖
    if "--db" in rest:
        idx = rest.index("--db")
        if idx + 1 < len(rest):
            config.db_path = Path(rest[idx + 1])
            rest = rest[:idx] + rest[idx + 2 :]

    store = SqliteStore(config.db_path)

    if cmd == "search":
        _cmd_search(rest, config, store)
    elif cmd in ("trending", "hot"):
        _cmd_trending(rest, config, store)
    elif cmd == "extract":
        _cmd_extract(rest, config, store)
    elif cmd == "stats":
        _cmd_stats(store)
    elif cmd == "recent":
        _cmd_recent(rest, store)
    elif cmd == "digest":
        _cmd_digest(store)
    elif cmd == "topics":
        _cmd_topics(store)
    else:
        print(f"未知命令: {cmd}")
        print(_HELP)


def _cmd_search(args: list, config: CrawlerConfig, store: SqliteStore) -> None:
    if len(args) < 2:
        print("用法: scrawl search <source> <query> [--limit N]")
        return
    source_name, query = args[0], args[1]
    limit = _get_opt(args, "--limit", 10)

    source = _load_source(source_name, config)
    if not source:
        return

    t0 = time.time()
    results = source.search(query, limit=limit)
    elapsed = int((time.time() - t0) * 1000)

    new = store.save_batch(results)
    store.log_crawl(source_name, "search", query, len(results), elapsed)

    print(f"✅ [{source_name}] 搜索 '{query}': {len(results)}条 (新增{new}) {elapsed}ms")
    for r in results[:5]:
        print(f"  • {r.title[:60]}  {r.url[:50]}")


def _cmd_trending(args: list, config: CrawlerConfig, store: SqliteStore) -> None:
    source_name = args[0] if args else "hackernews"
    limit = _get_opt(args, "--limit", 20)

    source = _load_source(source_name, config)
    if not source:
        return

    t0 = time.time()
    results = source.trending(limit=limit)
    elapsed = int((time.time() - t0) * 1000)

    new = store.save_batch(results)
    store.log_crawl(source_name, "trending", "", len(results), elapsed)

    print(f"🔥 [{source_name}] 趋势: {len(results)}条 (新增{new}) {elapsed}ms")
    for r in results[:10]:
        metrics = ""
        if r.metrics.get("stars"):
            metrics += f" ⭐{r.metrics['stars']}"
        if r.metrics.get("votes"):
            metrics += f" 👍{r.metrics['votes']}"
        if r.metrics.get("points"):
            metrics += f" 📊{r.metrics['points']}"
        print(f"  • {r.title[:55]}{metrics}")


def _cmd_extract(args: list, config: CrawlerConfig, store: SqliteStore) -> None:
    if not args:
        print("用法: scrawl extract <url>")
        return
    url = args[0]

    from .sources.web_generic import WebGenericSource
    web = WebGenericSource(config)
    result = web.extract(url)
    if result:
        store.save(result)
        print(f"✅ {result.title}")
        print(f"   内容长度: {len(result.content)} 字符")
    else:
        print("❌ 抓取失败")


def _cmd_stats(store: SqliteStore) -> None:
    stats = store.stats()
    print(f"📊 数据库统计")
    print(f"  总条目: {stats['total']}")
    print(f"  今日新增: {stats['today']}")
    print(f"  按来源:")
    for src, cnt in stats["by_source"].items():
        print(f"    {src}: {cnt}")


def _cmd_recent(args: list, store: SqliteStore) -> None:
    source = args[0] if args else ""
    limit = _get_opt(args, "--limit", 10)
    items = store.recent(source=source, limit=limit)
    for item in items:
        print(f"  [{item['source']}] {item['title'][:50]}")
        print(f"    {item['url'][:70]}")


def _cmd_digest(store: SqliteStore) -> None:
    draft = generate_daily_digest(store)
    print(draft)


def _cmd_topics(store: SqliteStore) -> None:
    draft = generate_topic_suggestions(store)
    print(draft)


def _load_source(name: str, config: CrawlerConfig):
    """动态加载数据源"""
    from .sources import ALL_SOURCES

    cls = ALL_SOURCES.get(name)
    if not cls:
        print(f"未知数据源: {name}")
        print(f"可用: {', '.join(ALL_SOURCES.keys())}")
        return None
    return cls(config)


def _get_opt(args: list, key: str, default) -> any:
    if key in args:
        idx = args.index(key)
        if idx + 1 < len(args):
            val = args[idx + 1]
            return int(val) if isinstance(default, int) else val
    return default


_HELP = """Super Crawler — 可复用多源数据采集框架

用法:
  scrawl search <source> <query> [--limit N]   搜索
  scrawl trending <source> [--limit N]         获取趋势
  scrawl extract <url>                         抓取单个URL
  scrawl stats                                 数据库统计
  scrawl recent [source] [--limit N]           最近条目
  scrawl digest                                生成每日速报草稿
  scrawl topics                                生成选题建议

数据源:
  github         GitHub仓库搜索
  arxiv          arXiv论文
  hackernews     HackerNews讨论
  producthunt    ProductHunt新品
  web            通用网页(Firecrawl)
  semantic_scholar  SemanticScholar(需安装)

示例:
  scrawl search github "AI agent"
  scrawl trending hackernews --limit 10
  scrawl trending producthunt
  scrawl digest --db ~/projects/startup/data/factory.db
"""
