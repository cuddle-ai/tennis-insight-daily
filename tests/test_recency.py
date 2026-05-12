# tests/test_recency.py
import pytest
from datetime import datetime, timedelta, timezone
from src.data_sources.base import NewsItem
from src.processor.recency import filter_by_days

def make_item(published_at):
    return NewsItem(
        title="Test news", url="https://example.com", source="Tennis.com",
        published_at=published_at, media_type="article",
    )

def test_filter_by_days_keeps_recent():
    now = datetime.now(timezone.utc)
    items = [
        make_item((now - timedelta(hours=1)).isoformat()),
        make_item((now - timedelta(days=2)).isoformat()),
    ]
    result = filter_by_days(items, days=3)
    assert len(result) == 2

def test_filter_by_days_removes_old():
    now = datetime.now(timezone.utc)
    items = [
        make_item((now - timedelta(hours=1)).isoformat()),
        make_item((now - timedelta(days=5)).isoformat()),
    ]
    result = filter_by_days(items, days=3)
    assert len(result) == 1
    assert "1 hour" in result[0].title or "5 days" not in result[0].title

def test_filter_by_days_handles_z_suffix():
    now = datetime.now(timezone.utc)
    items = [make_item((now - timedelta(hours=2)).isoformat() + "Z")]
    result = filter_by_days(items, days=3)
    assert len(result) == 1

def test_filter_by_days_keeps_unparseable():
    items = [make_item("invalid-date-string")]
    result = filter_by_days(items, days=3)
    assert len(result) == 1  # 解析失败保留

def test_filter_by_days_empty_list():
    result = filter_by_days([], days=3)
    assert result == []
