# tests/test_ai_summary.py
import pytest
from unittest.mock import MagicMock
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
