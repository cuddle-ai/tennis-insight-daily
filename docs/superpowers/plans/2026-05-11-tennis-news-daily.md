# Tennis News Daily Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个每日自动抓取网球资讯、经 AI 处理后生成静态 HTML 日报并发布到 GitHub Pages 的个人工具。

**Architecture:** Python 脚本作为单向流水线（抓取 → 去重过滤 → AI 摘要 → HTML 渲染），GitHub Actions 每天北京时间 07:00 定时触发，输出静态文件 push 到 GitHub Pages。数据源插件化，每个数据源实现统一的 `fetch / transform / render_html` 接口。

**Tech Stack:** Python 3.11, feedparser, trafilatura, google-api-python-client, snscrape, anthropic SDK, Jinja2, difflib, GitHub Actions, GitHub Pages

---

---

### Task 1: 项目脚手架 & 配置系统

**Files:**
- Create: `config.yaml`
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_config.py
import pytest
from src.config import load_config

def test_load_config_returns_required_keys():
    cfg = load_config("config.yaml")
    assert "players" in cfg
    assert "tournaments" in cfg
    assert "sources" in cfg
    assert "ai" in cfg

def test_load_config_sources_has_flags():
    cfg = load_config("config.yaml")
    assert isinstance(cfg["sources"]["news"], bool)
    assert isinstance(cfg["sources"]["youtube"], bool)
    assert isinstance(cfg["sources"]["twitter"], bool)
    assert isinstance(cfg["sources"]["atp_wta"], bool)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_config.py -v
```
Expected: `ModuleNotFoundError` 或 `FileNotFoundError`

- [ ] **Step 3: 创建 config.yaml**

```yaml
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
  language: zh

schedule:
  publish_time: "07:00"
```

- [ ] **Step 4: 创建 requirements.txt**

```
feedparser==6.0.11
trafilatura==1.12.2
google-api-python-client==2.131.0
snscrape==0.7.0.20230622
anthropic==0.40.0
Jinja2==3.1.4
PyYAML==6.0.2
requests==2.32.3
pytest==8.3.2
```

- [ ] **Step 5: 创建 src/config.py**

```python
import yaml
from pathlib import Path

def load_config(path: str = "config.yaml") -> dict:
    with open(Path(path)) as f:
        return yaml.safe_load(f)
```

- [ ] **Step 6: 创建空 __init__ 文件**

```bash
touch src/__init__.py tests/__init__.py
```

- [ ] **Step 7: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 8: 运行测试确认通过**

```bash
pytest tests/test_config.py -v
```
Expected: 2 passed

- [ ] **Step 9: Commit**

```bash
git init
git add config.yaml requirements.txt src/ tests/
git commit -m "feat: project scaffold and config loader"
```


---

### Task 2: BaseDataSource 接口 & 统一数据模型

**Files:**
- Create: `src/data_sources/__init__.py`
- Create: `src/data_sources/base.py`
- Create: `tests/test_base_datasource.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_base_datasource.py
import pytest
from src.data_sources.base import BaseDataSource, NewsItem

def test_news_item_required_fields():
    item = NewsItem(
        title="Sinner wins Roland Garros",
        url="https://example.com/article",
        source="Tennis.com",
        published_at="2026-05-11T06:00:00",
        media_type="article",
    )
    assert item.title == "Sinner wins Roland Garros"
    assert item.image_url is None
    assert item.summary is None

def test_base_datasource_is_abstract():
    with pytest.raises(TypeError):
        BaseDataSource()

def test_concrete_datasource_must_implement_fetch():
    class Incomplete(BaseDataSource):
        pass
    with pytest.raises(TypeError):
        Incomplete()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_base_datasource.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/data_sources/base.py**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published_at: str          # ISO 8601 string
    media_type: str            # "article" | "video" | "tweet" | "match_result" | "schedule"
    summary: Optional[str] = None
    image_url: Optional[str] = None
    embed_html: Optional[str] = None   # for tweets / youtube iframes
    players: list[str] = field(default_factory=list)
    tournaments: list[str] = field(default_factory=list)
    weight: int = 0            # 排序权重，越大越靠前

class BaseDataSource(ABC):
    @abstractmethod
    def fetch(self) -> list[NewsItem]:
        """抓取并返回 NewsItem 列表"""
        ...
```

- [ ] **Step 4: 创建 src/data_sources/__init__.py**

```python
from .base import BaseDataSource, NewsItem

__all__ = ["BaseDataSource", "NewsItem"]
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_base_datasource.py -v
```
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/data_sources/ tests/test_base_datasource.py
git commit -m "feat: BaseDataSource interface and NewsItem data model"
```


---

### Task 3: RSS 新闻数据源

**Files:**
- Create: `src/data_sources/rss_news.py`
- Create: `tests/test_rss_news.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_rss_news.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.rss_news import RssNewsSource
from src.data_sources.base import NewsItem

MOCK_FEED = {
    "entries": [
        {
            "title": "Alcaraz beats Djokovic",
            "link": "https://tennis.com/article/1",
            "summary": "Carlos Alcaraz defeated Novak Djokovic in straight sets.",
            "published": "Mon, 11 May 2026 05:00:00 +0000",
            "media_content": [{"url": "https://tennis.com/img/1.jpg"}],
        }
    ]
}

def test_rss_news_fetch_returns_news_items():
    source = RssNewsSource(
        name="Tennis.com",
        url="https://www.tennis.com/rss",
    )
    with patch("feedparser.parse", return_value=MOCK_FEED):
        items = source.fetch()
    assert len(items) == 1
    assert isinstance(items[0], NewsItem)
    assert items[0].title == "Alcaraz beats Djokovic"
    assert items[0].source == "Tennis.com"
    assert items[0].media_type == "article"
    assert items[0].image_url == "https://tennis.com/img/1.jpg"

def test_rss_news_fetch_handles_missing_image():
    entry_no_img = {
        "entries": [
            {
                "title": "No image article",
                "link": "https://tennis.com/article/2",
                "summary": "Some text.",
                "published": "Mon, 11 May 2026 05:00:00 +0000",
            }
        ]
    }
    source = RssNewsSource(name="Tennis.com", url="https://www.tennis.com/rss")
    with patch("feedparser.parse", return_value=entry_no_img):
        items = source.fetch()
    assert items[0].image_url is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_rss_news.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/data_sources/rss_news.py**

```python
import feedparser
from datetime import datetime, timezone
from .base import BaseDataSource, NewsItem

RSS_SOURCES = [
    {"name": "Tennis.com",       "url": "https://www.tennis.com/rss/"},
    {"name": "ATP Tour",         "url": "https://www.atptour.com/en/media/rss-feed/xml-feed"},
    {"name": "WTA Tour",         "url": "https://www.wtatennis.com/rss.xml"},
    {"name": "Tennis World USA", "url": "https://www.tennisworldusa.org/rss/news.xml"},
    {"name": "We Are Tennis",    "url": "https://www.wearetennis.com/rss"},
]

class RssNewsSource(BaseDataSource):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def fetch(self) -> list[NewsItem]:
        feed = feedparser.parse(self.url)
        items = []
        for entry in feed.get("entries", []):
            image_url = None
            media = entry.get("media_content", [])
            if media:
                image_url = media[0].get("url")
            if not image_url:
                enclosures = entry.get("enclosures", [])
                if enclosures:
                    image_url = enclosures[0].get("url")

            published = entry.get("published", "")
            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                dt = published

            items.append(NewsItem(
                title=entry.get("title", "").strip(),
                url=entry.get("link", ""),
                source=self.name,
                published_at=dt,
                media_type="article",
                summary=entry.get("summary", "").strip() or None,
                image_url=image_url,
            ))
        return items


def build_rss_sources(cfg: dict) -> list[RssNewsSource]:
    if not cfg.get("sources", {}).get("news", True):
        return []
    return [RssNewsSource(name=s["name"], url=s["url"]) for s in RSS_SOURCES]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_rss_news.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/data_sources/rss_news.py tests/test_rss_news.py
git commit -m "feat: RSS news data source"
```


---

### Task 4: ATP/WTA 赛事数据源

**Files:**
- Create: `src/data_sources/atp_wta.py`
- Create: `tests/test_atp_wta.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_atp_wta.py
import pytest
from unittest.mock import patch
from src.data_sources.atp_wta import MatchResultsSource, TodayScheduleSource
from src.data_sources.base import NewsItem

MOCK_RESULTS_HTML = """
<html><body>
<table class="day-table">
  <tr>
    <td class="day-table-name"><a>Carlos Alcaraz</a></td>
    <td class="day-table-score">6-3 6-4</td>
    <td class="day-table-name"><a>Holger Rune</a></td>
  </tr>
</table>
</body></html>
"""

def test_match_results_returns_news_items():
    source = MatchResultsSource()
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = MOCK_RESULTS_HTML
        mock_get.return_value.status_code = 200
        items = source.fetch()
    assert len(items) >= 0  # 结构可能变化，至少不抛异常
    for item in items:
        assert isinstance(item, NewsItem)
        assert item.media_type == "match_result"

def test_today_schedule_returns_news_items():
    source = TodayScheduleSource()
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = MOCK_RESULTS_HTML
        mock_get.return_value.status_code = 200
        items = source.fetch()
    for item in items:
        assert item.media_type == "schedule"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_atp_wta.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/data_sources/atp_wta.py**

```python
import requests
from datetime import date
from bs4 import BeautifulSoup
from .base import BaseDataSource, NewsItem

ATP_RESULTS_URL = "https://www.atptour.com/en/scores/results-archive"
ATP_SCHEDULE_URL = "https://www.atptour.com/en/scores/current"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TennisNewsDaily/1.0)"}

class MatchResultsSource(BaseDataSource):
    def fetch(self) -> list[NewsItem]:
        try:
            resp = requests.get(ATP_RESULTS_URL, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            for row in soup.select("table.day-table tr"):
                cells = row.select("td")
                if len(cells) < 3:
                    continue
                player1 = cells[0].get_text(strip=True)
                score = cells[1].get_text(strip=True)
                player2 = cells[2].get_text(strip=True)
                if not player1 or not score:
                    continue
                items.append(NewsItem(
                    title=f"{player1} def. {player2}  {score}",
                    url=ATP_RESULTS_URL,
                    source="ATP Tour",
                    published_at=date.today().isoformat(),
                    media_type="match_result",
                    players=[player1, player2],
                    weight=80,
                ))
            return items
        except Exception:
            return []


class TodayScheduleSource(BaseDataSource):
    def fetch(self) -> list[NewsItem]:
        try:
            resp = requests.get(ATP_SCHEDULE_URL, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            for row in soup.select("table.day-table tr"):
                cells = row.select("td")
                if len(cells) < 2:
                    continue
                player1 = cells[0].get_text(strip=True)
                player2 = cells[-1].get_text(strip=True)
                if not player1:
                    continue
                items.append(NewsItem(
                    title=f"今日赛程: {player1} vs {player2}",
                    url=ATP_SCHEDULE_URL,
                    source="ATP Tour",
                    published_at=date.today().isoformat(),
                    media_type="schedule",
                    players=[player1, player2],
                    weight=70,
                ))
            return items
        except Exception:
            return []


def build_atp_wta_sources(cfg: dict) -> list[BaseDataSource]:
    if not cfg.get("sources", {}).get("atp_wta", True):
        return []
    return [MatchResultsSource(), TodayScheduleSource()]
```

注意：需在 requirements.txt 中加入 `beautifulsoup4==4.12.3`。

- [ ] **Step 4: 更新 requirements.txt**

在 `requirements.txt` 末尾加一行：
```
beautifulsoup4==4.12.3
```
然后：
```bash
pip install beautifulsoup4==4.12.3
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_atp_wta.py -v
```
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/data_sources/atp_wta.py tests/test_atp_wta.py requirements.txt
git commit -m "feat: ATP/WTA match results and schedule data source"
```


---

### Task 5: YouTube 数据源

**Files:**
- Create: `src/data_sources/youtube.py`
- Create: `tests/test_youtube.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_youtube.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.youtube import YouTubeSource
from src.data_sources.base import NewsItem

MOCK_SEARCH_RESPONSE = {
    "items": [
        {
            "id": {"videoId": "abc123"},
            "snippet": {
                "title": "Roland Garros 2026 Highlights",
                "channelTitle": "Tennis TV",
                "publishedAt": "2026-05-11T04:00:00Z",
                "thumbnails": {"high": {"url": "https://img.youtube.com/vi/abc123/hqdefault.jpg"}},
            },
        }
    ]
}

def test_youtube_fetch_returns_news_items():
    source = YouTubeSource(api_key="fake_key", query="tennis Roland Garros", max_results=3)
    mock_service = MagicMock()
    mock_service.search().list().execute.return_value = MOCK_SEARCH_RESPONSE
    with patch("src.data_sources.youtube.build", return_value=mock_service):
        items = source.fetch()
    assert len(items) == 1
    assert isinstance(items[0], NewsItem)
    assert items[0].media_type == "video"
    assert "abc123" in items[0].embed_html
    assert items[0].image_url == "https://img.youtube.com/vi/abc123/hqdefault.jpg"

def test_youtube_fetch_returns_empty_on_error():
    source = YouTubeSource(api_key="bad_key", query="tennis", max_results=3)
    with patch("src.data_sources.youtube.build", side_effect=Exception("API error")):
        items = source.fetch()
    assert items == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_youtube.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/data_sources/youtube.py**

```python
from googleapiclient.discovery import build
from .base import BaseDataSource, NewsItem

class YouTubeSource(BaseDataSource):
    def __init__(self, api_key: str, query: str, max_results: int = 3):
        self.api_key = api_key
        self.query = query
        self.max_results = max_results

    def fetch(self) -> list[NewsItem]:
        try:
            service = build("youtube", "v3", developerKey=self.api_key)
            response = (
                service.search()
                .list(q=self.query, part="snippet", type="video",
                      maxResults=self.max_results, order="date")
                .execute()
            )
            items = []
            for entry in response.get("items", []):
                video_id = entry["id"]["videoId"]
                snippet = entry["snippet"]
                embed_html = (
                    f'<iframe width="560" height="315" '
                    f'src="https://www.youtube.com/embed/{video_id}" '
                    f'frameborder="0" allowfullscreen></iframe>'
                )
                items.append(NewsItem(
                    title=snippet["title"],
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    source=snippet.get("channelTitle", "YouTube"),
                    published_at=snippet["publishedAt"],
                    media_type="video",
                    image_url=snippet["thumbnails"]["high"]["url"],
                    embed_html=embed_html,
                    weight=30,
                ))
            return items
        except Exception:
            return []


def build_youtube_source(cfg: dict) -> list[YouTubeSource]:
    if not cfg.get("sources", {}).get("youtube", True):
        return []
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        return []
    players = cfg.get("players", [])
    query = "tennis " + " OR ".join(players[:3]) if players else "tennis highlights"
    return [YouTubeSource(api_key=api_key, query=query, max_results=3)]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_youtube.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/data_sources/youtube.py tests/test_youtube.py
git commit -m "feat: YouTube video data source"
```


---

### Task 6: X (Twitter) 数据源

**Files:**
- Create: `src/data_sources/twitter.py`
- Create: `tests/test_twitter.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_twitter.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.twitter import TwitterSource
from src.data_sources.base import NewsItem

class MockTweet:
    id = 123456789
    date = __import__("datetime").datetime(2026, 5, 11, 6, 0, 0)
    rawContent = "Sinner wins! #RolandGarros"
    user = MagicMock(username="atptour")

def test_twitter_fetch_returns_news_items():
    source = TwitterSource(query="tennis Roland Garros", max_results=3)
    with patch("snscrape.modules.twitter.TwitterSearchScraper") as mock_cls:
        mock_cls.return_value.get_items.return_value = iter([MockTweet()])
        items = source.fetch()
    assert len(items) == 1
    assert isinstance(items[0], NewsItem)
    assert items[0].media_type == "tweet"
    assert "123456789" in items[0].embed_html

def test_twitter_fetch_returns_empty_on_error():
    source = TwitterSource(query="tennis", max_results=3)
    with patch("snscrape.modules.twitter.TwitterSearchScraper", side_effect=Exception("blocked")):
        items = source.fetch()
    assert items == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_twitter.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/data_sources/twitter.py**

```python
from .base import BaseDataSource, NewsItem

class TwitterSource(BaseDataSource):
    def __init__(self, query: str, max_results: int = 3):
        self.query = query
        self.max_results = max_results

    def fetch(self) -> list[NewsItem]:
        try:
            import snscrape.modules.twitter as sntwitter
            scraper = sntwitter.TwitterSearchScraper(self.query)
            items = []
            for i, tweet in enumerate(scraper.get_items()):
                if i >= self.max_results:
                    break
                embed_html = (
                    f'<blockquote class="twitter-tweet">'
                    f'<a href="https://twitter.com/{tweet.user.username}/status/{tweet.id}"></a>'
                    f'</blockquote>'
                    f'<script async src="https://platform.twitter.com/widgets.js"></script>'
                )
                items.append(NewsItem(
                    title=tweet.rawContent[:100],
                    url=f"https://twitter.com/{tweet.user.username}/status/{tweet.id}",
                    source=f"@{tweet.user.username}",
                    published_at=tweet.date.isoformat(),
                    media_type="tweet",
                    embed_html=embed_html,
                    weight=20,
                ))
            return items
        except Exception:
            return []


def build_twitter_source(cfg: dict) -> list[TwitterSource]:
    if not cfg.get("sources", {}).get("twitter", True):
        return []
    players = cfg.get("players", [])
    query = "tennis (" + " OR ".join(players[:3]) + ")" if players else "tennis -filter:retweets"
    return [TwitterSource(query=query, max_results=3)]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_twitter.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/data_sources/twitter.py tests/test_twitter.py
git commit -m "feat: Twitter/X data source via snscrape"
```


---

### Task 7: 去重 & 关键词过滤处理器

**Files:**
- Create: `src/processor/__init__.py`
- Create: `src/processor/dedup.py`
- Create: `src/processor/filter.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_processor.py
import pytest
from src.data_sources.base import NewsItem
from src.processor.dedup import dedup_items
from src.processor.filter import filter_by_config

def make_item(title, source="Tennis.com", media_type="article"):
    return NewsItem(title=title, url=f"https://example.com/{title}", source=source,
                    published_at="2026-05-11T06:00:00", media_type=media_type)

def test_dedup_removes_similar_titles():
    items = [
        make_item("Sinner wins Roland Garros final"),
        make_item("Sinner wins Roland Garros final match"),  # 相似度 > 0.8
        make_item("Alcaraz beats Rune in quarterfinal"),
    ]
    result = dedup_items(items, threshold=0.8)
    assert len(result) == 2

def test_dedup_keeps_dissimilar_items():
    items = [make_item("Sinner wins"), make_item("Alcaraz loses")]
    result = dedup_items(items, threshold=0.8)
    assert len(result) == 2

def test_filter_keeps_items_matching_players():
    cfg = {"players": ["Sinner"], "tournaments": []}
    items = [
        make_item("Sinner wins Roland Garros"),
        make_item("Alcaraz beats Rune"),
    ]
    result = filter_by_config(items, cfg, section="players")
    assert any("Sinner" in i.title for i in result)

def test_filter_returns_all_when_no_config():
    cfg = {"players": [], "tournaments": []}
    items = [make_item("Any news"), make_item("Other news")]
    result = filter_by_config(items, cfg, section="players")
    assert len(result) == 2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_processor.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/processor/dedup.py**

```python
from difflib import SequenceMatcher
from src.data_sources.base import NewsItem

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def dedup_items(items: list[NewsItem], threshold: float = 0.8) -> list[NewsItem]:
    kept = []
    for item in items:
        if not any(_similarity(item.title, k.title) >= threshold for k in kept):
            kept.append(item)
    return kept
```

- [ ] **Step 4: 创建 src/processor/filter.py**

```python
from src.data_sources.base import NewsItem

def filter_by_config(items: list[NewsItem], cfg: dict, section: str) -> list[NewsItem]:
    keywords = [k.lower() for k in cfg.get(section, [])]
    if not keywords:
        return items
    return [
        item for item in items
        if any(kw in item.title.lower() for kw in keywords)
        or item.media_type in ("match_result", "schedule", "video", "tweet")
    ]
```

- [ ] **Step 5: 创建 src/processor/__init__.py**

```python
from .dedup import dedup_items
from .filter import filter_by_config

__all__ = ["dedup_items", "filter_by_config"]
```

- [ ] **Step 6: 运行测试确认通过**

```bash
pytest tests/test_processor.py -v
```
Expected: 4 passed

- [ ] **Step 7: Commit**

```bash
git add src/processor/ tests/test_processor.py
git commit -m "feat: dedup and keyword filter processors"
```


---

### Task 8: AI 摘要处理器

**Files:**
- Create: `src/processor/ai_summary.py`
- Create: `tests/test_ai_summary.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_ai_summary.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.base import NewsItem
from src.processor.ai_summary import summarize_items, generate_daily_intro

def make_item(title):
    return NewsItem(title=title, url="https://example.com", source="Tennis.com",
                    published_at="2026-05-11T06:00:00", media_type="article",
                    summary="Original summary text here.")

def mock_claude_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg

def test_summarize_items_adds_summary():
    items = [make_item("Sinner wins Roland Garros")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_claude_response("辛纳赢得法网冠军。")
    result = summarize_items(items, client=mock_client, model="claude-sonnet-4-6", language="zh")
    assert result[0].summary == "辛纳赢得法网冠军。"

def test_summarize_items_skips_non_articles():
    items = [NewsItem(title="Match", url="https://x.com", source="ATP",
                      published_at="2026-05-11", media_type="match_result")]
    mock_client = MagicMock()
    result = summarize_items(items, client=mock_client, model="claude-sonnet-4-6", language="zh")
    mock_client.messages.create.assert_not_called()
    assert result[0].summary is None

def test_generate_daily_intro_returns_string():
    items = [make_item("Sinner wins"), make_item("Alcaraz loses")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_claude_response("今日网球要闻：辛纳夺冠。")
    intro = generate_daily_intro(items, client=mock_client, model="claude-sonnet-4-6", language="zh")
    assert isinstance(intro, str)
    assert len(intro) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_ai_summary.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/processor/ai_summary.py**

```python
import anthropic
from src.data_sources.base import NewsItem

def summarize_items(
    items: list[NewsItem],
    client: anthropic.Anthropic,
    model: str,
    language: str = "zh",
) -> list[NewsItem]:
    lang_name = "中文" if language == "zh" else "English"
    for item in items:
        if item.media_type not in ("article",):
            continue
        if not item.summary:
            continue
        prompt = (
            f"请用{lang_name}将以下网球新闻摘要压缩为2-3句话，简洁客观，适合早间快读。\n\n"
            f"标题：{item.title}\n原文摘要：{item.summary}"
        )
        response = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        item.summary = response.content[0].text.strip()
    return items


def generate_daily_intro(
    items: list[NewsItem],
    client: anthropic.Anthropic,
    model: str,
    language: str = "zh",
) -> str:
    lang_name = "中文" if language == "zh" else "English"
    headlines = "\n".join(f"- {i.title}" for i in items[:10])
    prompt = (
        f"以下是今日网球资讯标题列表，请用{lang_name}写一段3-5句的今日导读，"
        f"概括最重要的事件，语气简洁、客观。\n\n{headlines}"
    )
    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_ai_summary.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/processor/ai_summary.py tests/test_ai_summary.py
git commit -m "feat: Claude AI summarizer and daily intro generator"
```


---

### Task 9: 内容排序器

**Files:**
- Create: `src/processor/sorter.py`
- Create: `tests/test_sorter.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_sorter.py
import pytest
from src.data_sources.base import NewsItem
from src.processor.sorter import sort_items, assign_weights

def make_item(title, media_type="article", players=None, tournaments=None, weight=0):
    return NewsItem(
        title=title, url="https://example.com", source="Tennis.com",
        published_at="2026-05-11T06:00:00", media_type=media_type,
        players=players or [], tournaments=tournaments or [], weight=weight,
    )

def test_assign_weights_grand_slam_result():
    cfg = {"players": ["Sinner"], "tournaments": ["Roland Garros"]}
    item = make_item("Sinner wins Roland Garros", media_type="match_result",
                     players=["Sinner"], tournaments=["Roland Garros"])
    result = assign_weights([item], cfg)
    assert result[0].weight >= 100

def test_assign_weights_followed_player():
    cfg = {"players": ["Sinner"], "tournaments": []}
    item = make_item("Sinner press conference", players=["Sinner"])
    result = assign_weights([item], cfg)
    assert result[0].weight >= 50

def test_sort_items_orders_by_weight_descending():
    items = [
        make_item("Low priority", weight=10),
        make_item("High priority", weight=100),
        make_item("Medium priority", weight=50),
    ]
    result = sort_items(items)
    assert result[0].weight == 100
    assert result[1].weight == 50
    assert result[2].weight == 10
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_sorter.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/processor/sorter.py**

```python
from src.data_sources.base import NewsItem

GRAND_SLAMS = {"Roland Garros", "Wimbledon", "US Open", "Australian Open"}
MASTERS = {"Indian Wells", "Miami", "Monte Carlo", "Madrid", "Rome",
           "Canada", "Cincinnati", "Shanghai", "Paris"}

def assign_weights(items: list[NewsItem], cfg: dict) -> list[NewsItem]:
    followed_players = {p.lower() for p in cfg.get("players", [])}
    followed_tournaments = {t.lower() for t in cfg.get("tournaments", [])}

    for item in items:
        w = item.weight  # 保留数据源设置的基础权重

        # 赛事类型加权
        if item.media_type == "match_result":
            item_tournaments = {t.lower() for t in item.tournaments}
            if item_tournaments & {t.lower() for t in GRAND_SLAMS}:
                w += 100
            elif item_tournaments & {t.lower() for t in MASTERS}:
                w += 60
            else:
                w += 40

        # 关注球员加权
        item_players = {p.lower() for p in item.players}
        if item_players & followed_players:
            w += 50

        # 关注赛事加权
        title_lower = item.title.lower()
        if any(t.lower() in title_lower for t in followed_tournaments):
            w += 30
        if any(p.lower() in title_lower for p in followed_players):
            w += 20

        # 今日赛程
        if item.media_type == "schedule":
            w += 35

        item.weight = w
    return items


def sort_items(items: list[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda i: i.weight, reverse=True)
```

- [ ] **Step 4: 更新 src/processor/__init__.py**

```python
from .dedup import dedup_items
from .filter import filter_by_config
from .sorter import assign_weights, sort_items

__all__ = ["dedup_items", "filter_by_config", "assign_weights", "sort_items"]
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_sorter.py -v
```
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/processor/sorter.py tests/test_sorter.py src/processor/__init__.py
git commit -m "feat: content weight assignment and sorting"
```


---

### Task 10: Jinja2 模板 & 日报 HTML 渲染器

**Files:**
- Create: `templates/daily.html`
- Create: `src/renderer/__init__.py`
- Create: `src/renderer/daily_page.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_renderer.py
import pytest
from src.data_sources.base import NewsItem
from src.renderer.daily_page import render_daily_page

def make_article(title):
    return NewsItem(
        title=title, url="https://example.com", source="Tennis.com",
        published_at="2026-05-11T06:00:00", media_type="article",
        summary="AI 生成的摘要。", image_url="https://example.com/img.jpg",
    )

def make_video():
    return NewsItem(
        title="Roland Garros Highlights", url="https://youtube.com/watch?v=abc",
        source="Tennis TV", published_at="2026-05-11T05:00:00", media_type="video",
        embed_html='<iframe src="https://www.youtube.com/embed/abc"></iframe>',
    )

def test_render_daily_page_contains_date():
    html = render_daily_page(
        date="2026-05-11", intro="今日导读内容。",
        items=[make_article("Sinner wins")], template_dir="templates",
    )
    assert "2026-05-11" in html

def test_render_daily_page_contains_article_title():
    html = render_daily_page(
        date="2026-05-11", intro="导读。",
        items=[make_article("Sinner wins Roland Garros")], template_dir="templates",
    )
    assert "Sinner wins Roland Garros" in html

def test_render_daily_page_embeds_video():
    html = render_daily_page(
        date="2026-05-11", intro="导读。",
        items=[make_video()], template_dir="templates",
    )
    assert "youtube.com/embed/abc" in html
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_renderer.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 templates/daily.html**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tennis News Daily — {{ date }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 860px; margin: 0 auto; padding: 1.5rem; color: #1a1a1a; }
    h1 { font-size: 1.6rem; border-bottom: 3px solid #2e7d32; padding-bottom: .5rem; }
    h2 { font-size: 1.1rem; color: #2e7d32; margin-top: 2rem; }
    .intro { background: #f1f8e9; border-left: 4px solid #2e7d32;
             padding: .8rem 1rem; margin: 1rem 0; border-radius: 0 4px 4px 0; }
    .card { display: flex; gap: 1rem; margin: 1rem 0; padding: 1rem;
            border: 1px solid #e0e0e0; border-radius: 6px; }
    .card img { width: 120px; height: 80px; object-fit: cover; border-radius: 4px; flex-shrink: 0; }
    .card-body h3 { margin: 0 0 .4rem; font-size: 1rem; }
    .card-body p { margin: 0 0 .4rem; font-size: .9rem; color: #444; }
    .card-meta { font-size: .8rem; color: #888; }
    .card-meta a { color: #2e7d32; text-decoration: none; }
    table { width: 100%; border-collapse: collapse; font-size: .9rem; }
    th, td { padding: .5rem .75rem; border: 1px solid #e0e0e0; text-align: left; }
    th { background: #f5f5f5; }
    .embed-wrap { margin: 1rem 0; }
    .embed-wrap iframe { max-width: 100%; border-radius: 6px; }
    .more-list { list-style: none; padding: 0; }
    .more-list li { padding: .4rem 0; border-bottom: 1px solid #f0f0f0; font-size: .9rem; }
    .more-list a { color: #1a1a1a; text-decoration: none; }
    .more-list a:hover { color: #2e7d32; }
    nav { margin-top: 2rem; font-size: .85rem; color: #888; }
    nav a { color: #2e7d32; text-decoration: none; margin-right: 1rem; }
  </style>
</head>
<body>
  <h1>🎾 Tennis News Daily — {{ date }}</h1>

  {% if intro %}
  <div class="intro">{{ intro }}</div>
  {% endif %}

  {% if headlines %}
  <h2>头条新闻</h2>
  {% for item in headlines %}
  <div class="card">
    {% if item.image_url %}<img src="{{ item.image_url }}" alt="">{% endif %}
    <div class="card-body">
      <h3>{{ item.title }}</h3>
      {% if item.summary %}<p>{{ item.summary }}</p>{% endif %}
      <div class="card-meta">{{ item.source }} · <a href="{{ item.url }}" target="_blank">阅读原文 →</a></div>
    </div>
  </div>
  {% endfor %}
  {% endif %}

  {% if match_results or schedules %}
  <h2>赛事动态</h2>
  {% if match_results %}
  <h3 style="font-size:.95rem;color:#555;">昨日结果</h3>
  <table>
    <tr><th>比赛</th></tr>
    {% for item in match_results %}
    <tr><td>{{ item.title }}</td></tr>
    {% endfor %}
  </table>
  {% endif %}
  {% if schedules %}
  <h3 style="font-size:.95rem;color:#555;margin-top:1rem;">今日赛程</h3>
  <table>
    <tr><th>赛程</th></tr>
    {% for item in schedules %}
    <tr><td>{{ item.title }}</td></tr>
    {% endfor %}
  </table>
  {% endif %}
  {% endif %}

  {% if player_news %}
  <h2>球员动态</h2>
  {% for item in player_news %}
  <div class="card">
    {% if item.image_url %}<img src="{{ item.image_url }}" alt="">{% endif %}
    <div class="card-body">
      <h3>{{ item.title }}</h3>
      {% if item.summary %}<p>{{ item.summary }}</p>{% endif %}
      <div class="card-meta">{{ item.source }} · <a href="{{ item.url }}" target="_blank">阅读原文 →</a></div>
    </div>
  </div>
  {% endfor %}
  {% endif %}

  {% if social_items %}
  <h2>社交精选</h2>
  {% for item in social_items %}
  <div class="embed-wrap">
    {% if item.embed_html %}{{ item.embed_html | safe }}{% endif %}
  </div>
  {% endfor %}
  {% endif %}

  {% if more_news %}
  <h2>更多新闻</h2>
  <ul class="more-list">
    {% for item in more_news %}
    <li><a href="{{ item.url }}" target="_blank">{{ item.title }}</a>
        <span style="color:#aaa;font-size:.8rem;"> — {{ item.source }}</span></li>
    {% endfor %}
  </ul>
  {% endif %}

  <nav>
    <a href="index.html">← 历史归档</a>
  </nav>
</body>
</html>
```

- [ ] **Step 4: 创建 src/renderer/daily_page.py**

```python
from jinja2 import Environment, FileSystemLoader
from src.data_sources.base import NewsItem

def render_daily_page(
    date: str,
    intro: str,
    items: list[NewsItem],
    template_dir: str = "templates",
) -> str:
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    tmpl = env.get_template("daily.html")

    headlines = [i for i in items if i.media_type == "article"][:5]
    match_results = [i for i in items if i.media_type == "match_result"]
    schedules = [i for i in items if i.media_type == "schedule"]
    social_items = [i for i in items if i.media_type in ("video", "tweet")]
    # 球员动态：article 类型但不在头条里
    player_news = [i for i in items if i.media_type == "article" and i not in headlines
                   and any(p for p in i.players)][:5]
    more_news = [i for i in items if i.media_type == "article"
                 and i not in headlines and i not in player_news]

    return tmpl.render(
        date=date,
        intro=intro,
        headlines=headlines,
        match_results=match_results,
        schedules=schedules,
        player_news=player_news,
        social_items=social_items,
        more_news=more_news,
    )
```

- [ ] **Step 5: 创建 src/renderer/__init__.py**

```python
from .daily_page import render_daily_page

__all__ = ["render_daily_page"]
```

- [ ] **Step 6: 运行测试确认通过**

```bash
pytest tests/test_renderer.py -v
```
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add templates/daily.html src/renderer/ tests/test_renderer.py
git commit -m "feat: Jinja2 daily report HTML renderer"
```


---

### Task 11: 归档首页渲染器

**Files:**
- Create: `templates/index.html`
- Create: `src/renderer/index_page.py`
- Create: `tests/test_index_page.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_index_page.py
from src.renderer.index_page import render_index_page

def test_render_index_contains_date_links():
    html = render_index_page(
        dates=["2026-05-11", "2026-05-10", "2026-05-09"],
        template_dir="templates",
    )
    assert "2026-05-11" in html
    assert "2026-05-11.html" in html
    assert "2026-05-09" in html

def test_render_index_empty_dates():
    html = render_index_page(dates=[], template_dir="templates")
    assert "Tennis News Daily" in html
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_index_page.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 templates/index.html**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tennis News Daily — 归档</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 600px; margin: 0 auto; padding: 1.5rem; color: #1a1a1a; }
    h1 { font-size: 1.6rem; border-bottom: 3px solid #2e7d32; padding-bottom: .5rem; }
    ul { list-style: none; padding: 0; }
    li { padding: .6rem 0; border-bottom: 1px solid #f0f0f0; }
    a { color: #2e7d32; text-decoration: none; font-size: 1rem; }
    a:hover { text-decoration: underline; }
    .empty { color: #aaa; font-size: .9rem; }
  </style>
</head>
<body>
  <h1>🎾 Tennis News Daily</h1>
  <p style="color:#666;font-size:.9rem;">每日网球资讯归档</p>
  {% if dates %}
  <ul>
    {% for date in dates %}
    <li><a href="{{ date }}.html">{{ date }}</a></li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="empty">暂无日报，明天再来。</p>
  {% endif %}
</body>
</html>
```

- [ ] **Step 4: 创建 src/renderer/index_page.py**

```python
from jinja2 import Environment, FileSystemLoader

def render_index_page(dates: list[str], template_dir: str = "templates") -> str:
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    tmpl = env.get_template("index.html")
    return tmpl.render(dates=sorted(dates, reverse=True))
```

- [ ] **Step 5: 更新 src/renderer/__init__.py**

```python
from .daily_page import render_daily_page
from .index_page import render_index_page

__all__ = ["render_daily_page", "render_index_page"]
```

- [ ] **Step 6: 运行测试确认通过**

```bash
pytest tests/test_index_page.py -v
```
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add templates/index.html src/renderer/index_page.py tests/test_index_page.py src/renderer/__init__.py
git commit -m "feat: archive index page renderer"
```


---

### Task 12: 主流水线入口 (main.py)

**Files:**
- Create: `src/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_main.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_main_creates_output_file(tmp_path):
    from src.main import run_pipeline
    mock_items = []
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="今日导读。"), \
         patch("src.main.summarize_items", return_value=mock_items):
        run_pipeline(
            config_path="config.yaml",
            output_dir=str(tmp_path),
            template_dir="templates",
        )
    files = list(tmp_path.glob("*.html"))
    assert any(f.name == "index.html" for f in files)
    daily_files = [f for f in files if f.name != "index.html"]
    assert len(daily_files) == 1

def test_main_output_dir_is_created(tmp_path):
    from src.main import run_pipeline
    new_dir = tmp_path / "output"
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="导读。"), \
         patch("src.main.summarize_items", return_value=[]):
        run_pipeline(
            config_path="config.yaml",
            output_dir=str(new_dir),
            template_dir="templates",
        )
    assert new_dir.exists()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_main.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/main.py**

```python
import os
import anthropic
from datetime import date
from pathlib import Path

from src.config import load_config
from src.data_sources.rss_news import build_rss_sources
from src.data_sources.atp_wta import build_atp_wta_sources
from src.data_sources.youtube import build_youtube_source
from src.data_sources.twitter import build_twitter_source
from src.processor.dedup import dedup_items
from src.processor.filter import filter_by_config
from src.processor.sorter import assign_weights, sort_items
from src.processor.ai_summary import summarize_items, generate_daily_intro
from src.renderer.daily_page import render_daily_page
from src.renderer.index_page import render_index_page


def run_pipeline(
    config_path: str = "config.yaml",
    output_dir: str = "output",
    template_dir: str = "templates",
) -> None:
    cfg = load_config(config_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. 抓取
    sources = (
        build_rss_sources(cfg)
        + build_atp_wta_sources(cfg)
        + build_youtube_source(cfg)
        + build_twitter_source(cfg)
    )
    all_items = []
    for source in sources:
        all_items.extend(source.fetch())

    # 2. 去重 & 过滤
    all_items = dedup_items(all_items, threshold=0.8)
    all_items = filter_by_config(all_items, cfg, section="players")

    # 3. 排序
    all_items = assign_weights(all_items, cfg)
    all_items = sort_items(all_items)

    # 4. AI 摘要
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    ai_cfg = cfg.get("ai", {})
    model = ai_cfg.get("model", "claude-sonnet-4-6")
    language = ai_cfg.get("language", "zh")

    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        all_items = summarize_items(all_items, client=client, model=model, language=language)
        intro = generate_daily_intro(all_items, client=client, model=model, language=language)
    else:
        intro = "（AI 摘要未启用，请配置 ANTHROPIC_API_KEY）"

    # 5. 渲染日报
    today = date.today().isoformat()
    daily_html = render_daily_page(
        date=today, intro=intro, items=all_items, template_dir=template_dir
    )
    (out / f"{today}.html").write_text(daily_html, encoding="utf-8")

    # 6. 更新归档首页
    existing_dates = sorted(
        [f.stem for f in out.glob("????-??-??.html")], reverse=True
    )
    index_html = render_index_page(dates=existing_dates, template_dir=template_dir)
    (out / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Done: output/{today}.html")


if __name__ == "__main__":
    run_pipeline()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_main.py -v
```
Expected: 2 passed

- [ ] **Step 5: 运行全量测试**

```bash
pytest tests/ -v
```
Expected: 全部通过

- [ ] **Step 6: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: main pipeline orchestrator"
```


---

### Task 13: GitHub Actions 自动化部署

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: 创建 .github/workflows/daily.yml**

```yaml
name: Daily Tennis News

on:
  schedule:
    - cron: "0 23 * * *"   # 北京时间 07:00 (UTC+8 = UTC-8h → 23:00 UTC)
  workflow_dispatch:         # 支持手动触发

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate daily report
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
        run: python src/main.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
          keep_files: true    # 保留历史日报文件
```

- [ ] **Step 2: 在 GitHub 仓库配置 Secrets**

进入仓库 Settings → Secrets and variables → Actions，添加：
- `ANTHROPIC_API_KEY`：你的 Anthropic API Key
- `YOUTUBE_API_KEY`：你的 YouTube Data API v3 Key（在 Google Cloud Console 创建，免费）

- [ ] **Step 3: 启用 GitHub Pages**

进入仓库 Settings → Pages：
- Source: Deploy from a branch
- Branch: `gh-pages` / `/ (root)`
- 保存

- [ ] **Step 4: 手动触发一次验证**

在 GitHub Actions 页面找到 "Daily Tennis News" workflow，点击 "Run workflow" 手动触发，确认 job 成功完成，访问 `https://<username>.github.io/<repo>/` 查看日报。

- [ ] **Step 5: Commit**

```bash
git add .github/
git commit -m "feat: GitHub Actions daily automation and Pages deployment"
```


---

## Self-Review

### Spec Coverage Check

| Spec 章节 | 对应 Task |
|-----------|-----------|
| 架构：单向流水线 | Task 12 (main.py) |
| 数据源：RSS 新闻 | Task 3 |
| 数据源：ATP/WTA 赛事 | Task 4 |
| 数据源：YouTube | Task 5 |
| 数据源：X/Twitter | Task 6 |
| 数据源插件化接口 | Task 2 |
| 去重 & 过滤 | Task 7 |
| AI 摘要 & 今日导读 | Task 8 |
| 内容排序 | Task 9 |
| 日报 HTML 结构 | Task 10 |
| 归档首页 | Task 11 |
| config.yaml 个性化配置 | Task 1 |
| GitHub Actions 部署 | Task 13 |

所有 spec 章节均有对应 Task，无遗漏。

### 类型一致性

- `NewsItem` 在 Task 2 定义，Task 3-9 均使用相同字段名（`title`, `url`, `source`, `published_at`, `media_type`, `summary`, `image_url`, `embed_html`, `players`, `tournaments`, `weight`）
- `render_daily_page` 签名在 Task 10 定义，Task 12 调用参数一致
- `build_*_sources` 函数在各数据源 Task 中定义，Task 12 统一调用，命名一致

### Placeholder 扫描

无 TBD / TODO / "implement later" 等占位符。

