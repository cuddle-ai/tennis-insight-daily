# tests/test_rss_news.py
import pytest
from unittest.mock import patch
from src.data_sources.rss_news import RssNewsSource
from src.data_sources.base import NewsItem

MOCK_FEED = {
    "entries": [
        {
            "title": "Alcaraz beats Djokovic",
            "link": "https://tennis.com/article/1",
            "summary": "Carlos Alcaraz defeated Novak Djokovic in straight sets.",
            "published": "Mon, 11 May 2026 05:00:00 +0000",
            "published_parsed": (2026, 5, 11, 5, 0, 0, 0, 0, 0),
            "media_content": [{"url": "https://tennis.com/img/1.jpg"}],
        }
    ]
}

def test_rss_news_fetch_returns_news_items():
    source = RssNewsSource(name="Tennis.com", url="https://www.tennis.com/rss")
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
                "published_parsed": (2026, 5, 11, 5, 0, 0, 0, 0, 0),
            }
        ]
    }
    source = RssNewsSource(name="Tennis.com", url="https://www.tennis.com/rss")
    with patch("feedparser.parse", return_value=entry_no_img):
        items = source.fetch()
    assert items[0].image_url is None
