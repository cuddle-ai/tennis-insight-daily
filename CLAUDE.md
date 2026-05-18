# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

```bash
# 安装依赖（Playwright 用于 Twitter 抓取）
pip install -r requirements.txt
playwright install chromium

# 运行测试
pytest tests/ -v

# 运行日报生成（默认采集昨天，北京时间）
python src/main.py

# 指定日期
TARGET_DATE=2026-05-15 python src/main.py
```

## 架构概述

每日网球资讯聚合器，T-1 模式采集前一天（北京时间）资讯，经 AI 总结后输出静态 HTML。

```
数据源 (data_sources/) → 处理器 (processor/) → 渲染器 (renderer/)
     ↓                      ↓                  ↓
  fetch() 返回          dedup → filter →    Jinja2 模板
  list[NewsItem]        date_range → sort →  输出 HTML
                        weight → summarize
```

### T-1 模式

日期边界以北京时间（UTC+8）为准。例如 5 月 17 日的日报覆盖 UTC 5/16 16:00 ~ 5/17 16:00 的资讯。可通过 `TARGET_DATE` 环境变量指定任意日期。

### 数据源注册模式

每个数据源模块提供 `build_<name>_source(cfg) -> list[BaseDataSource]` 函数：
- 检查 `cfg["sources"]["<name>"]` 决定是否启用
- 返回空列表 `[]` 表示禁用
- 新增数据源：在 `src/main.py` 的 sources 列表中追加调用即可

当前数据源：
- `rss_news.py` — BBC Sport + ESPN Tennis RSS
- `atp_wta.py` — ATP 赛果 + 今日赛程（网页抓取）
- `youtube.py` — YouTube Data API v3，按频道 ID 查询
- `twitter.py` — Playwright 无头浏览器抓取 x.com（需登录，未登录只能抓固定推文）
- `apify_instagram.py` — Apify API 抓取 Instagram（免费额度已耗尽）

### 关键接口

**NewsItem** (`src/data_sources/base.py`)：所有数据流转的核心数据结构
```python
@dataclass
class NewsItem:
    title: str; url: str; source: str; published_at: str  # ISO 8601
    media_type: str  # "article"|"video"|"tweet"|"match_result"|"schedule"|"instagram"
    summary: Optional[str] = None; image_url: Optional[str] = None
    embed_html: Optional[str] = None
    players/tournaments: list[str]; weight: int = 0  # 排序权重
```

**BaseDataSource**：抽象基类，子类实现 `fetch() -> list[NewsItem]`

### 处理器链

`src/main.py` 中的处理顺序：
1. `trace_dedup` — 标题相似度去重（threshold=0.8）
2. `filter_by_config` — 按 players/tournaments 过滤（当前为 no-op，仅作排序信号）
3. `trace_date_range` — T-1 日期范围过滤，只保留目标日期的条目
4. `assign_weights` — 按媒体类型 + 赛事级别 + 关注球员加权
5. `sort_items` — 按 weight 降序
6. `summarize_items` + `generate_daily_intro` — AI 总结（如有 API key）
7. `render_daily_page` — 渲染 daily.html
8. `render_index_page` — 更新 index.html 归档索引

### 权重体系

`sorter.py` 中的评分逻辑（越高越靠前）：
- 媒体类型：match_result > schedule > video > tweet/instagram
- 赛事级别：四大满贯 > Masters 1000 > 其他
- 关注球员：标题中出现 +50，任意位置出现 +20

### AI 集成

使用 OpenAI 兼容接口（阿里 DashScope），模型 `qwen3.6-max-preview`。由 `AI_LANGUAGE` 控制输出语言（`"zh"` / `"en"`）。无 API key 时优雅降级，跳过总结步骤。

### 配置

配置通过 `.env` 文件（本地）或环境变量（远端）加载，`src/config.py` 合并两个来源（环境变量优先）。密钥类配置通过环境变量注入，不写入代码。

## 注意事项

- Twitter 抓取依赖 Playwright + JS 注入（`twitter.py` 中的 `_SCRAPE_JS`），x.com 未登录只显示固定推文（约 2020-2022 年）
- `instagram.py`（直接抓取）从未在 pipeline 中使用，Instagram 仅通过 Apify 获取
- 所有测试使用 pytest + `unittest.mock.patch` 隔离外部依赖
- `src/time_utils.py` 提供时间解析和日期范围过滤，日期边界基于北京时间（UTC+8）
- `src/debug_report.py` 提供 pipeline 各阶段追踪和调试报告（`DEBUG_REPORT_ENABLED=true` 开启）
