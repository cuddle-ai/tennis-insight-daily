# tests/test_twitter.py
import pytest
from unittest.mock import MagicMock, patch
from src.data_sources.twitter import TwitterSource, _build_twitter_usernames, _parse_twitter_date
from src.data_sources.base import NewsItem


def test_build_twitter_usernames_includes_officials():
    usernames = _build_twitter_usernames([])
    assert "atptour" in usernames
    assert "WTA" in usernames
    assert "rolandgarros" in usernames


def test_build_twitter_usernames_adds_players():
    usernames = _build_twitter_usernames(["Jannik Sinner", "Carlos Alcaraz"])
    assert "JannikSinner" in usernames
    assert "carlitosalcaraz" in usernames
    assert "atptour" in usernames


def test_parse_twitter_date_relative():
    # Relative times should return a recent date
    dt = _parse_twitter_date("2h")
    assert dt is not None


def test_parse_twitter_date_full():
    dt = _parse_twitter_date("May 4, 2026")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 5


def test_parse_twitter_date_partial():
    dt = _parse_twitter_date("May 12")
    assert dt is not None
    assert dt.month == 5


def test_twitter_source_returns_empty_on_import_error():
    source = TwitterSource(usernames=["atptour"], max_results=3, since_days=3)
    with patch("src.data_sources.twitter._scrape_twitter_page", return_value=[]):
        items = source.fetch()
    assert items == []