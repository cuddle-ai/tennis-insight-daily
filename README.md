# Tennis Insight Daily

每日 AI 网球资讯聚合器。T-1 模式采集前一天（北京时间）的资讯，经去重、加权排序、AI 摘要后输出为静态 HTML 页面。

![Python](https://img.shields.io/badge/Python-3.11+-3c873a?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

## Features

- **T-1 模式**：按北京时间日历日期采集，每天的内容边界清晰不重叠
- **多源聚合**：RSS（BBC/ESPN）、ATP/WTA 赛果赛程、YouTube、Twitter/X、Instagram
- **AI 摘要**：基于阿里 DashScope 生成每日导语和条目摘要
- **调试报告**：pipeline 各阶段的完整追踪，便于排查数据问题

## Quick Start

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 复制配置模板并填入实际值
cp .env.example .env

# 运行（默认采集昨天）
python src/main.py

# 指定日期
TARGET_DATE=2026-05-15 python src/main.py
```

输出文件位于 `output/YYYY-MM-DD.html`。

## Configuration

所有配置通过环境变量或 `.env` 文件传入（环境变量优先）。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PLAYERS` | 关注球员（逗号分隔） | 空 |
| `TOURNAMENTS` | 关注赛事（逗号分隔） | 空 |
| `SOURCES_NEWS` | 启用 RSS 新闻源 | `true` |
| `SOURCES_ATP_WTA` | 启用 ATP/WTA 数据源 | `true` |
| `SOURCES_YOUTUBE` | 启用 YouTube 数据源 | `true` |
| `SOURCES_TWITTER` | 启用 Twitter 数据源 | `true` |
| `SOURCES_INSTAGRAM` | 启用 Instagram 数据源 | `true` |
| `CONTENT_HEADLINES_LIMIT` | 头条新闻上限 | `8` |
| `CONTENT_SOCIAL_LIMIT` | 社交精选上限 | `5` |
| `AI_MODEL` | AI 模型名称 | `qwen3.6-max-preview` |
| `AI_BASE_URL` | OpenAI 兼容 API 地址 | 空 |
| `AI_API_KEY` | API 密钥 | 空 |
| `AI_LANGUAGE` | 输出语言 | `zh` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 密钥 | 空 |
| `APIFY_API_KEY` | Apify API 密钥（Instagram） | 空 |
| `TARGET_DATE` | 指定目标日期（YYYY-MM-DD） | 昨天（北京时间） |
| `DEBUG_REPORT_ENABLED` | 生成调试报告 | `false` |

## Architecture

```
数据源 → 处理器 → 渲染器

src/data_sources/          src/processor/           src/renderer/
  fetch() → list[NewsItem]   dedup → filter →          Jinja2 模板
                             date_range → sort →       输出 HTML
                             weight → summarize
```

**数据源** (`src/data_sources/`)：每个数据源实现 `BaseDataSource` 抽象类，提供 `fetch() -> list[NewsItem]` 方法，通过 `build_<name>_source(cfg)` 注册。

**处理器** (`src/processor/`)：管道式处理链，包括去重、配置过滤、日期范围过滤、权重计算、AI 摘要。

**渲染器** (`src/renderer/`)：Jinja2 模板输出 HTML。`daily_page.py` 生成日报，`index_page.py` 生成归档索引。

## Data Sources

| Source | 文件 | 说明 |
|---|---|---|
| RSS | `rss_news.py` | BBC Sport + ESPN Tennis |
| ATP/WTA | `atp_wta.py` | 赛果 + 今日赛程（网页抓取） |
| YouTube | `youtube.py` | 按频道 ID 查询 YouTube Data API v3 |
| Twitter/X | `twitter.py` | Playwright 无头浏览器抓取 |
| Instagram | `apify_instagram.py` | Apify API |

## Testing

```bash
pytest tests/ -v
```

测试使用 `unittest.mock.patch` 隔离外部依赖，无需真实 API Key。

## Project Structure

```
.
├── .env.example               # 配置模板
├── requirements.txt           # Python 依赖
├── src/
│   ├── main.py                # Pipeline 入口
│   ├── config.py              # 配置加载
│   ├── time_utils.py          # 时间解析与日期范围过滤（CST）
│   ├── debug_report.py        # Pipeline 追踪与调试报告
│   ├── data_sources/          # 数据源插件
│   │   ├── base.py            # BaseDataSource + NewsItem
│   │   ├── rss_news.py
│   │   ├── atp_wta.py
│   │   ├── youtube.py
│   │   ├── twitter.py
│   │   └── apify_instagram.py
│   ├── processor/             # 数据处理
│   │   ├── dedup.py
│   │   ├── filter.py
│   │   ├── recency.py
│   │   ├── sorter.py
│   │   └── ai_summary.py
│   └── renderer/              # HTML 输出
│       ├── daily_page.py
│       └── index_page.py
├── templates/                 # Jinja2 模板
│   ├── daily.html
│   ├── index.html
│   └── debug_report.html
├── output/                    # 生成文件（gitignore）
└── tests/                     # pytest 测试
```

## License

MIT
