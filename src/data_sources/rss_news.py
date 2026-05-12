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

            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                dt = entry.get("published", "")

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
