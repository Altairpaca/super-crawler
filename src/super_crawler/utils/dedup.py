"""URL/内容去重"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


class Deduplicator:
    """基于SQLite的去重器。

    用法:
        dedup = Deduplicator(db_path)
        if not dedup.seen("https://example.com"):
            # ... 抓取 ...
            dedup.mark("https://example.com", title="Example")
    """

    def __init__(self, db_path: Path | str, table: str = "dedup_log"):
        self.db_path = Path(db_path)
        self.table = table
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                source TEXT,
                first_seen TEXT DEFAULT (datetime('now', 'localtime')),
                last_seen TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def _hash(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def seen(self, url: str) -> bool:
        """检查URL是否已抓取过"""
        h = self._hash(url)
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute(
            f"SELECT 1 FROM {self.table} WHERE url_hash=?", (h,)
        ).fetchone()
        conn.close()
        return row is not None

    def mark(self, url: str, title: str = "", source: str = "") -> None:
        """标记URL为已抓取"""
        h = self._hash(url)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(f"""
            INSERT OR REPLACE INTO {self.table}
            (url_hash, url, title, source, last_seen)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
        """, (h, url, title, source))
        conn.commit()
        conn.close()

    def stats(self) -> dict:
        """去重统计"""
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()[0]
        today = conn.execute(
            f"SELECT COUNT(*) FROM {self.table} WHERE first_seen >= date('now')"
        ).fetchone()[0]
        conn.close()
        return {"total": total, "today": today}
