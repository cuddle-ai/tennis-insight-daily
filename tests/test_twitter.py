# tests/test_twitter.py
import sys
import types
import pytest
from unittest.mock import MagicMock, patch
from src.data_sources.twitter import TwitterSource
from src.data_sources.base import NewsItem


def _make_snscrape_mock(tweets):
    """注入一个假的 snscrape.modules.twitter 到 sys.modules"""
    mock_tweet = MagicMock()
    mock_tweet.id = 123456789
    mock_tweet.date = __import__("datetime").datetime(2026, 5, 11, 6, 0, 0)
    mock_tweet.rawContent = "Sinner wins! #RolandGarros"
    mock_tweet.user = MagicMock(username="atptour")

    mock_scraper = MagicMock()
    mock_scraper.get_items.return_value = iter(tweets)

    mock_twitter_mod = MagicMock()
    mock_twitter_mod.TwitterSearchScraper.return_value = mock_scraper

    mock_modules_pkg = types.ModuleType("snscrape.modules")
    mock_modules_pkg.twitter = mock_twitter_mod

    mock_snscrape = types.ModuleType("snscrape")
    mock_snscrape.modules = mock_modules_pkg

    return mock_snscrape, mock_modules_pkg, mock_twitter_mod, mock_tweet


def test_twitter_fetch_returns_news_items():
    mock_snscrape, mock_modules_pkg, mock_twitter_mod, mock_tweet = _make_snscrape_mock([mock_tweet := MagicMock(
        id=123456789,
        date=__import__("datetime").datetime(2026, 5, 11, 6, 0, 0),
        rawContent="Sinner wins! #RolandGarros",
        user=MagicMock(username="atptour"),
    )])

    with patch.dict(sys.modules, {
        "snscrape": mock_snscrape,
        "snscrape.modules": mock_modules_pkg,
        "snscrape.modules.twitter": mock_twitter_mod,
    }):
        source = TwitterSource(query="tennis Roland Garros", max_results=3)
        items = source.fetch()

    assert len(items) == 1
    assert isinstance(items[0], NewsItem)
    assert items[0].media_type == "tweet"
    assert "123456789" in items[0].embed_html


def test_twitter_fetch_returns_empty_on_error():
    source = TwitterSource(query="tennis", max_results=3)
    # snscrape 不在 sys.modules 中，import 会失败，fetch 应返回 []
    with patch.dict(sys.modules, {"snscrape": None}):
        items = source.fetch()
    assert items == []
