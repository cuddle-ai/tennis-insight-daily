# Tennis News Daily — Product Design Spec

**Date:** 2026-05-11
**Status:** Approved

---

## 1. Overview

Tennis News Daily 是一个面向网球爱好者的个人日报工具。每天早上自动抓取主流网球新闻、赛事动态和社交媒体内容，经 AI 处理后生成一份富媒体日报，发布到 GitHub Pages 供用户浏览，并支持历史归档。

**核心用户场景：** 用户每天早上打开网页，看到一份已整理好的网球资讯，包含头条新闻（含图片）、赛事动态、关注球员动态、YouTube 视频精选和 X 推文精选。

---

## 2. 架构

```
[数据源层]                [处理层]                  [输出层]
RSS / 网页抓取   →
ATP/WTA 赛事页  →   Python 脚本                →   静态 HTML 日报
YouTube API    →   (抓取 → 去重过滤 → AI 摘要 → 渲染)    ↓
X (snscrape)   →                               GitHub Pages
                          ↑                    (历史归档)
                   GitHub Actions
                   (每天早上定时触发，北京时间 07:00)
```

整个系统是单向流水线，无服务器、无数据库。所有历史日报以静态文件形式存储在 Git 仓库中。

---

## 3. 数据源

### 3.1 新闻网站（文本 + 图片）

优先使用 RSS Feed，无 RSS 的站点用 `trafilatura` 抓取正文和首图。

| 来源 | 类型 | 备注 |
|------|------|------|
| Tennis.com | RSS | 英文主流 |
| ATP Tour 官网 | RSS / 抓取 | 官方赛事新闻 |
| WTA Tour 官网 | RSS / 抓取 | 官方赛事新闻 |
| Tennis World USA | RSS | 英文 |
| We Are Tennis | RSS | 英文 |
| 网球之家 | 抓取 | 中文 |

### 3.2 赛事数据

直接抓取 ATP/WTA 官网赛程和结果页面，提取：
- 昨日比赛结果（比分、晋级情况）
- 今日赛程（场次、时间、球员）
- 当前积分榜 Top 10（每周更新）

### 3.3 社交媒体

| 来源 | 方案 | 内容类型 |
|------|------|------|
| YouTube | YouTube Data API v3（免费额度 10,000 units/天） | 视频 iframe 嵌入 |
| X (Twitter) | `snscrape` 开源库 / Nitter 实例 | 推文 embed 卡片 |

所有社交媒体内容以嵌入方式呈现，不下载媒体文件。

---

## 4. 数据源插件化设计

参考 CloudFlare-AI-Insight-Daily 的模式，每个数据源实现统一接口：

```python
class BaseDataSource:
    def fetch(self) -> list[dict]:
        """抓取原始数据，返回统一格式列表"""
        ...

    def transform(self, raw: list[dict]) -> list[dict]:
        """转换为统一数据模型"""
        # 统一字段: title, summary, url, image_url, published_at, source, media_type
        ...

    def render_html(self, item: dict) -> str:
        """生成单条内容的 HTML 片段"""
        ...
```

数据源在 `config.yaml` 中注册，可按需启用/禁用。

---

## 5. AI 处理层

**步骤一：去重 & 过滤**
- 用标题相似度（`difflib.SequenceMatcher`）合并重复报道，阈值 0.8
- 按 `config.yaml` 中配置的球员/赛事关键词过滤不相关内容

**步骤二：AI 摘要生成**
- 调用通义千问（OpenAI 兼容接口，`openai` SDK，百炼平台）
- 每条新闻生成 2-3 句中文摘要
- 全篇生成一段"今日导读"（3-5 句，概括当天最重要的事）
- Prompt 风格：简洁、客观、适合早间快读

**步骤三：内容排序**
按重要性权重排序（规则写在配置里，不做 ML）：
1. 大满贯 / 大师赛赛事结果
2. 关注球员相关新闻
3. 一般赛事新闻
4. 球员动态 / 采访
5. 社交媒体精选

---

## 6. 日报结构

每份日报是独立 HTML 文件，命名 `YYYY-MM-DD.html`：

```
Tennis News Daily — 2026-05-11

┌─────────────────────────────────┐
│ 今日导读（AI 生成，3-5 句）        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 头条新闻（3-5 条）                │
│ [图片] 标题                      │
│ AI 摘要（2-3 句）                 │
│ 来源 · 时间 · 阅读原文 →          │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 赛事动态                         │
│ 昨日结果（紧凑表格）               │
│ 今日赛程（紧凑表格）               │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 球员动态（按 config 关注球员过滤）  │
│ 同头条新闻格式                    │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 社交精选                         │
│ YouTube 视频 iframe（2-3 个）     │
│ X 推文 embed（2-3 条）            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 更多新闻（标题列表，点击跳转原文）  │
└─────────────────────────────────┘
```

**归档首页** `index.html`：日历式列表，展示所有历史日报链接。

---

## 7. 个性化配置

```yaml
# config.yaml

players:
  - Jannik Sinner
  - Carlos Alcaraz
  - Zheng Qinwen

tournaments:
  - Roland Garros
  - Wimbledon
  - US Open
  - Australian Open

sources:
  news: true
  atp_wta: true
  youtube: true
  twitter: true

ai:
  model: claude-sonnet-4-6
  language: zh  # 摘要语言

schedule:
  publish_time: "07:00"  # 北京时间 (UTC+8)
```

---

## 8. 项目结构

```
tennis-news-daily/
├── .github/
│   └── workflows/
│       └── daily.yml          # GitHub Actions 定时任务
├── src/
│   ├── main.py                # 入口，编排整个流水线
│   ├── data_sources/
│   │   ├── base.py            # BaseDataSource 接口
│   │   ├── rss_news.py        # RSS 新闻抓取
│   │   ├── atp_wta.py         # 赛事数据抓取
│   │   ├── youtube.py         # YouTube API
│   │   └── twitter.py        # X / snscrape
│   ├── processor/
│   │   ├── dedup.py           # 去重
│   │   ├── filter.py          # 关键词过滤
│   │   └── ai_summary.py      # Claude API 摘要
│   └── renderer/
│       ├── daily_page.py      # 日报 HTML 渲染
│       └── index_page.py      # 归档首页渲染
├── templates/
│   ├── daily.html             # 日报 Jinja2 模板
│   └── index.html             # 归档首页模板
├── output/                    # 生成的静态文件（GitHub Pages 根目录）
│   ├── index.html
│   └── 2026-05-11.html
├── config.yaml                # 用户个性化配置
└── requirements.txt
```

---

## 9. 部署

**GitHub Actions 工作流（`.github/workflows/daily.yml`）：**
1. 每天北京时间 07:00 触发（cron: `0 23 * * *` UTC）
2. 安装 Python 依赖
3. 运行 `python src/main.py`
4. 将 `output/` 目录 push 到 `gh-pages` 分支
5. GitHub Pages 自动发布

**Secrets 配置（GitHub Repository Secrets）：**
- `DASHSCOPE_API_KEY`
- `YOUTUBE_API_KEY`

---

## 10. 技术栈

| 组件 | 选型 |
|------|------|
| 运行环境 | Python 3.11 |
| RSS 解析 | `feedparser` |
| 网页抓取 | `trafilatura` |
| YouTube | `google-api-python-client` |
| X 抓取 | `snscrape` |
| AI 摘要 | `openai` SDK（通义千问 qwen3.6-plus，百炼平台） |
| HTML 渲染 | `Jinja2` |
| 去重 | `difflib` |
| 定时触发 | GitHub Actions |
| 托管 | GitHub Pages |

---

## 11. 范围边界（MVP 不包含）

- 用户注册 / 多用户体系
- 邮件推送
- 评论 / 互动功能
- 移动端 App
- 实时比分（非日报场景）
- UI 个性化设置界面（配置通过 `config.yaml` 修改）
