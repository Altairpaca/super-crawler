# Super Crawler 🔍

可复用的多源数据采集框架 — 为 Hermes profiles 提供统一爬虫能力。

## 安装

```bash
# 开发模式安装（推荐）
cd ~/repos/super-crawler
pip install -e .

# 带完整依赖
pip install -e ".[full]"
```

## 快速开始

```python
from super_crawler import CrawlerConfig, CrawlerSource
from super_crawler.sources.github import GitHubSource
from super_crawler.storage.sqlite_store import SqliteStore

# 配置（指向不同项目的DB）
config = CrawlerConfig(db_path="~/projects/startup/data/factory.db")

# 使用
gh = GitHubSource(config)
results = gh.search("AI agent", limit=10)

# 存储
store = SqliteStore(config.db_path)
store.save_batch(results)
```

## CLI

```bash
scrawl search github "AI agent"           # 搜索
scrawl trending hackernews --limit 10     # 趋势
scrawl extract https://example.com        # 抓取URL
scrawl stats                              # 统计
scrawl digest                             # 每日速报草稿
scrawl topics                             # 选题建议
```

## 数据源

| Source | 需要 | 说明 |
|--------|------|------|
| `github` | gh CLI 或网络 | 仓库搜索、趋势 |
| `arxiv` | 网络 | 学术论文 |
| `hackernews` | 网络 | HN讨论（Algolia API） |
| `producthunt` | 网络 | 新产品（GraphQL API） |
| `web` | Firecrawl | 通用网页抓取 |
| `semantic_scholar` | `pip install semanticscholar` | 论文引用网络 |

## 配置

复制 `.env.example` 为 `.env` 并填入：

```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
FIRECRAWL_URL=http://localhost:3002
```

## 项目间共享

```bash
# 在任何项目中安装
cd ~/Clausula && pip install -e ~/repos/super-crawler
cd ~/projects/startup && pip install -e ~/repos/super-crawler

# 每个项目指向自己的DB
scrawl search github "AI" --db ~/Clausula/data/knowledge.db
scrawl search github "AI" --db ~/projects/startup/data/factory.db
```

## 目录结构

```
src/super_crawler/
├── base.py           # CrawlerSource 基类 + CrawlResult
├── config.py         # 配置管理
├── cli.py            # CLI入口
├── sources/          # 数据源
│   ├── github.py
│   ├── arxiv.py
│   ├── hackernews.py
│   ├── producthunt.py
│   ├── web_generic.py
│   └── semantic_scholar.py
├── storage/          # 存储
│   ├── sqlite_store.py
│   └── schemas.py
├── utils/            # 工具
│   ├── proxy.py
│   ├── rate_limit.py
│   ├── retry.py
│   ├── dedup.py
│   └── text.py
└── generators/       # 内容生成
    └── draft.py
```
