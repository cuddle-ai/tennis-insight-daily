# tests/test_recency.py
from datetime import date, datetime, timedelta, timezone

from src.data_sources.base import NewsItem
from src.processor.recency import filter_by_target_date

CST = timezone(timedelta(hours=8))


def make_item(published_at):
    return NewsItem(
        title="Test news", url="https://example.com", source="Tennis.com",
        published_at=published_at, media_type="article",
    )


def test_filter_keeps_items_on_target_date_cst():
    """Beijing date 2026-05-17 spans UTC 2026-05-16T16:00 to 2026-05-17T16:00."""
    target = date(2026, 5, 17)
    items = [
        make_item("2026-05-16T16:00:00+00:00"),  # Beijing 00:00
        make_item("2026-05-17T15:59:59+00:00"),  # Beijing 23:59:59
        make_item("2026-05-17T04:00:00Z"),        # Beijing 12:00
    ]
    result = filter_by_target_date(items, target=target)
    assert len(result) == 3


def test_filter_removes_items_outside_target_date_cst():
    target = date(2026, 5, 17)
    items = [
        make_item("2026-05-17T04:00:00+00:00"),   # Beijing 12:00 — in range
        make_item("2026-05-16T15:59:59+00:00"),   # Beijing 23:59:59 on May 16 — out
        make_item("2026-05-17T16:00:00+00:00"),   # Beijing 00:00 on May 18 — out
    ]
    result = filter_by_target_date(items, target=target)
    assert len(result) == 1


def test_filter_keeps_unparseable():
    target = date(2026, 5, 17)
    items = [make_item("invalid-date-string")]
    result = filter_by_target_date(items, target=target)
    assert len(result) == 1


def test_filter_empty_list():
    target = date(2026, 5, 17)
    result = filter_by_target_date([], target=target)
    assert result == []


def test_filter_default_target_is_yesterday_cst():
    yesterday = (datetime.now(CST) - timedelta(days=1)).date()
    start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=CST)
    items = [
        make_item(start.astimezone(timezone.utc).isoformat()),
        make_item((start + timedelta(hours=12)).astimezone(timezone.utc).isoformat()),
    ]
    result = filter_by_target_date(items)
    assert len(result) == 2
