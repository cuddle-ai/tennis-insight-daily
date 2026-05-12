# tests/test_instagram.py
import pytest
from unittest.mock import patch, MagicMock
from src.data_sources.instagram import InstagramSource, INSTAGRAM_ACCOUNTS

MOCK_HTML = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"SocialMediaPosting",
 "url":"https://www.instagram.com/p/ABC123xyz/","headline":"Alcaraz practice session",
 "image":"https://example.com/img.jpg","datePublished":"2026-05-11T10:00:00Z"}
</script>
</head></html>
"""

def test_instagram_source_parses_json_ld():
    source = InstagramSource(username="carlosalcaraz", max_posts=3)
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = MOCK_HTML
        mock_get.return_value = mock_resp
        items = source.fetch()
    assert len(items) == 1
    assert items[0].media_type == "instagram"
    assert "ABC123xyz" in items[0].embed_html
    assert items[0].source == "@carlosalcaraz (Instagram)"

def test_instagram_source_handles_http_error():
    source = InstagramSource(username="badaccount", max_posts=3)
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        items = source.fetch()
    assert items == []

def test_build_instagram_source_respects_config():
    from src.data_sources.instagram import build_instagram_source
    cfg = {"sources": {"instagram": True}, "players": ["Jannik Sinner", "Carlos Alcaraz"]}
    sources = build_instagram_source(cfg)
    usernames = [s.username for s in sources]
    assert "atptour" in usernames
    assert "sinner.official" in usernames
    assert "carlosalcaraz" in usernames

def test_build_instagram_source_disabled():
    from src.data_sources.instagram import build_instagram_source
    cfg = {"sources": {"instagram": False}}
    sources = build_instagram_source(cfg)
    assert sources == []
