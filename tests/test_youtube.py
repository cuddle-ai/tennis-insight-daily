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
    source = YouTubeSource(
        api_key="fake_key", channel_ids=["UCY_5h5zaSwN7Or4kIJDYNXA"], max_results=3
    )
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
    source = YouTubeSource(
        api_key="bad_key", channel_ids=["UCY_5h5zaSwN7Or4kIJDYNXA"], max_results=3
    )
    with patch("src.data_sources.youtube.build", side_effect=Exception("API error")):
        items = source.fetch()
    assert items == []
