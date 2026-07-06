"""统一数据库Schema"""

# 内容表 — 所有数据源共用
CONTENT_TABLE = """
CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT,
    content_type TEXT DEFAULT 'item',
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content TEXT,
    authors TEXT,            -- JSON array
    tags TEXT,               -- JSON array
    published TEXT,
    metrics TEXT,            -- JSON dict
    raw_data TEXT,           -- JSON dict (完整原始数据)
    content_hash TEXT UNIQUE,
    crawled_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

# 去重日志
DEDUP_TABLE = """
CREATE TABLE IF NOT EXISTS dedup_log (
    url_hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    source TEXT,
    first_seen TEXT DEFAULT (datetime('now', 'localtime')),
    last_seen TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

# 爬取任务日志
CRAWL_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    action TEXT NOT NULL,     -- search/trending/extract
    query TEXT,
    result_count INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ok',
    error_msg TEXT,
    started_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

# 内容生成草稿
DRAFTS_TABLE = """
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_type TEXT NOT NULL,     -- daily_digest/topic_suggest/article
    title TEXT,
    content TEXT NOT NULL,
    source_ids TEXT,              -- JSON array of content.id
    status TEXT DEFAULT 'pending', -- pending/reviewed/published
    platform TEXT,                -- zhihu/wechat/x/etc
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    published_at TEXT
);
"""

ALL_TABLES = [CONTENT_TABLE, DEDUP_TABLE, CRAWL_LOG_TABLE, DRAFTS_TABLE]
