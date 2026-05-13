# Tennis Insight Daily

每日 AI 网球资讯聚合器，自动抓取多个来源的新闻并通过 AI 生成摘要，输出为静态 HTML 页面，部署至 GitHub Pages。

![Python](https://img.shields.io/badge/Python-3.11+-3c873a?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Build](https://img.shields.io/github/actions/workflow/status/cuddle-ai/tennis-insight-daily/daily.yml?style=flat-square&label=Build)

## Overview

Tennis Insight Daily 从以下来源自动聚合网球资讯：

- **RSS** — BBC Sport Tennis、ESPN Tennis
- **ATP / WTA** — 赛果与今日赛程
- **YouTube** — ATP Tour、WTA、四大满贯等官方频道
- **X (Twitter)** — 官方机构与球员账号
- **Instagram** — via Apify API

所有内容经过去重、时效过滤、AI 加权排序后，由 AI 生成每日导语与摘要，最终输出为静态 HTML 并部署至 GitHub Pages。每天 UTC 23:00 自动运行。

## Getting Started

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 运行日报生成
python src/main.py
```

输出文件位于 `output/YYYY-MM-DD.html`。

### 触发 GitHub Actions

在仓库页面进入 **Actions → Daily Tennis News → Run workflow** 手动触发。

## Configuration

编辑 `config.yaml` 即可配置关注球员、数据源开关、时效阈值与 AI 模型：

```yaml
players:                       # 用于内容过滤与权重加成
  - Jannik Sinner
  - Carlos Alcaraz
  - Zheng Qinwen

tournaments:
  - Roland Garros
  - Wimbledon
  - US Open
  - Australian Open

sources:                      # 各数据源开关
  news: true
  atp_wta: true
  youtube: true
  twitter: true
  instagram: true

content:
  recency_days: 3             # 保留最近 N 天的内容

ai:
  model: qwen3.6-max-preview
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  api_key: your-key           # 建议通过环境变量 DASHSCOPE_API_KEY 传入
  language: zh                # 输出语言：zh 或 en
```

> [!WARNING]
> `config.yaml` 中的 API Key 已提交到 Git。请勿将密钥推送至远程仓库。生产环境建议通过 GitHub Secrets 或环境变量注入。

### 所需环境变量 / Secrets

| Variable | 说明 |
|---|---|
| `YOUTUBE_API_KEY` | [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) 密钥 |
| `APIFY_API_KEY` | [Apify](https://apify.com) 密钥（用于 Instagram 抓取） |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key（AI 摘要，可选） |

## Architecture

```
config.yaml
    │
    ▼
src/main.py  ──  Pipeline  ──  output/
    │                               │
    ├─ build_*_source(cfg)          │
    │   fetch() → list[NewsItem]     │
    │                               │
    ├─ dedup_items()                │
    ├─ filter_by_config()           │
    ├─ filter_by_days()             │
    ├─ assign_weights()             │   daily.html (当天日报)
    ├─ sort_items()                │   index.html (归档索引)
    ├─ summarize_items() (AI)       │
    ├─ generate_daily_intro() (AI)  │
    └─ render_daily_page()          ▼
```

**数据源** (`src/data_sources/`)：每个数据源实现 `BaseDataSource` 抽象类，提供 `fetch() -> list[NewsItem]` 方法，通过 `build_<name>_source(cfg)` 注册。

**处理器** (`src/processor/`)：管道式处理链，包括去重、配置过滤、时效过滤、权重计算、AI 摘要。

**渲染器** (`src/renderer/`)：使用 Jinja2 模板将处理后的数据输出为 HTML。

## Data Sources

| Source | 文件 | 说明 |
|---|---|---|
| RSS | `rss_news.py` | BBC Sport + ESPN Tennis RSS |
| ATP/WTA | `atp_wta.py` | 赛果网页抓取 + 今日赛程 |
| YouTube | `youtube.py` | 按频道 ID 查询 YouTube Data API v3 |
| Twitter/X | `twitter.py` | Playwright 无头浏览器抓取（需登录，未登录仅抓固定推文） |
| Instagram | `apify_instagram.py` | Apify API（需付费额度） |

> [!NOTE]
> Twitter/X 未登录用户只能看到固定推文（约 2020-2022 年）。如需抓取最新内容，需提供有效 Cookie 凭据。

## Testing

```bash
# 运行全部测试
pytest tests/ -v

# 运行单个文件
pytest tests/test_twitter.py -v
```

测试使用 `unittest.mock.patch` 隔离外部依赖，无需真实 API Key。

## Project Structure

```
.
├── config.yaml                  # 主配置文件
├── requirements.txt             # Python 依赖
├── src/
│   ├── main.py                  # Pipeline 入口
│   ├── config.py                 # 配置加载
│   ├── data_sources/             # 数据源插件
│   │   ├── base.py              # BaseDataSource + NewsItem
│   │   ├── rss_news.py
│   │   ├── atp_wta.py
│   │   ├── youtube.py
│   │   ├── twitter.py
│   │   └── apify_instagram.py
│   ├── processor/               # 数据处理
│   │   ├── dedup.py
│   │   ├── filter.py
│   │   ├── recency.py
│   │   ├── sorter.py
│   │   └── ai_summary.py
│   └── renderer/               # HTML 输出
│       ├── daily_page.py
│       └── index_page.py
├── templates/                   # Jinja2 模板
│   ├── daily.html
│   └── index.html
├── output/                      # 生成文件（git 跟踪）
└── tests/                       # pytest 测试
```