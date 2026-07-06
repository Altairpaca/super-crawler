"""SQLite统一存储"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime

from ..base import CrawlResult
from .schemas import ALL_TABLES


class SqliteStore:
    """统一SQLite存储。

    用法:
        store = SqliteStore("path/to/db.db")
        store.save_batch(results)
        recent = store.recent(source="github", limit=10)
    """

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _init_tables(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        for sql in ALL_TABLES:
            conn.execute(sql)
        conn.commit()
        conn.close()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def save(self, result: CrawlResult) -> bool:
        """保存单条结果。返回是否为新条目（去重）。"""
        conn = self._conn()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO content
                (source, source_id, content_type, title, url, content,
                 authors, tags, published, metrics, raw_data, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.source,
                result.raw.get("source_id", result.url),
                "item",
                result.title,
                result.url,
                result.content,
                json.dumps(result.authors, ensure_ascii=False),
                json.dumps(result.tags, ensure_ascii=False),
                result.published,
                json.dumps(result.metrics, ensure_ascii=False),
                json.dumps(result.raw, ensure_ascii=False),
                result.content_hash,
            ))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def save_batch(self, results: list[CrawlResult]) -> int:
        """批量保存。返回新增条目数。"""
        conn = self._conn()
        count = 0
        try:
            for r in results:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO content
                    (source, source_id, content_type, title, url, content,
                     authors, tags, published, metrics, raw_data, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.source,
                    r.raw.get("source_id", r.url),
                    "item",
                    r.title,
                    r.url,
                    r.content,
                    json.dumps(r.authors, ensure_ascii=False),
                    json.dumps(r.tags, ensure_ascii=False),
                    r.published,
                    json.dumps(r.metrics, ensure_ascii=False),
                    json.dumps(r.raw, ensure_ascii=False),
                    r.content_hash,
                ))
                count += cursor.rowcount > 0
            conn.commit()
        finally:
            conn.close()
        return count

    def recent(self, source: str = "", limit: int = 20) -> list[dict]:
        """获取最近的条目"""
        conn = self._conn()
        if source:
            rows = conn.execute(
                "SELECT * FROM content WHERE source=? ORDER BY crawled_at DESC LIMIT ?",
                (source, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM content ORDER BY crawled_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        conn.close()

        cols = ["id", "source", "source_id", "content_type", "title", "url",
                "content", "authors", "tags", "published", "metrics",
                "raw_data", "content_hash", "crawled_at", "updated_at"]
        return [dict(zip(cols, row)) for row in rows]

    def stats(self) -> dict:
        """数据库统计"""
        conn = self._conn()
        total = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
        by_source = dict(conn.execute(
            "SELECT source, COUNT(*) FROM content GROUP BY source"
        ).fetchall())
        today = conn.execute(
            "SELECT COUNT(*) FROM content WHERE crawled_at >= date('now')"
        ).fetchone()[0]
        conn.close()
        return {"total": total, "by_source": by_source, "today": today}

    def log_crawl(self, source: str, action: str, query: str = "",
                  result_count: int = 0, duration_ms: int = 0,
                  status: str = "ok", error_msg: str = "") -> None:
        """记录爬取日志"""
        conn = self._conn()
        conn.execute("""
            INSERT INTO crawl_log (source, action, query, result_count, duration_ms, status, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source, action, query, result_count, duration_ms, status, error_msg))
        conn.commit()
        conn.close()
