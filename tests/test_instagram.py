# tests/test_instagram.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.apify_instagram import ApifyInstagramSource, build_apify_instagram_source, INSTAGRAM_ACCOUNTS


def test_build_instagram_source_respects_config():
    cfg = {"sources": {"instagram": True}, "players": ["Jannik Sinner", "Carlos Alcaraz"]}
    sources = build_apify_instagram_source(cfg)
    assert len(sources) == 1
    assert "atptour" in sources[0].usernames
    assert "sinner.official" in sources[0].usernames
    assert "carlosalcaraz" in sources[0].usernames


def test_build_instagram_source_disabled():
    cfg = {"sources": {"instagram": False}}
    sources = build_apify_instagram_source(cfg)
    assert sources == []


def test_apify_source_returns_empty_without_api_key():
    source = ApifyInstagramSource(usernames=["atptour"], max_posts=3)
    with patch.dict("os.environ", {"APIFY_API_KEY": ""}):
        items = source.fetch()
    assert items == []


def test_apify_source_parses_api_response():
    source = ApifyInstagramSource(usernames=["carlosalcaraz"], max_posts=3)
    mock_raw = [{
        "url": "https://www.instagram.com/p/ABC123xyz/",
        "caption": "Alcaraz practice session",
        "displayUrl": "https://example.com/img.jpg",
        "timestamp": "2026-05-11T10:00:00Z",
    }]
    with patch.dict("os.environ", {"APIFY_API_KEY": "test-key"}):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": mock_raw}
            mock_post.return_value = mock_resp
            items = source.fetch()
    assert len(items) == 1
    assert items[0].media_type == "instagram"
    assert "ABC123xyz" in items[0].embed_html
    assert items[0].source == "@carlosalcaraz (Instagram)"