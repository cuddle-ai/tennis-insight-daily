from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from src.data_sources.base import NewsItem


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


CST = timezone(timedelta(hours=8))


def get_target_date_range(target: date | None = None) -> tuple[datetime, datetime]:
    """Return (start, end) UTC datetime boundaries for a Beijing-time calendar date.

    Defaults to yesterday (T-1) in Beijing time, so the pipeline triggered at
    Beijing 00:00 collects the previous full day's news using CST boundaries.
    """
    if target is None:
        now_cst = datetime.now(CST)
        target = (now_cst - timedelta(days=1)).date()
    start = datetime(target.year, target.month, target.day, tzinfo=CST).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def is_within_date_range(value: str | None, start: datetime, end: datetime) -> bool | None:
    dt = parse_datetime(value)
    if dt is None:
        return None
    return start <= dt < end


def filter_by_date_range(
    items: list[NewsItem],
    start: datetime,
    end: datetime,
    keep_unparseable: bool = True,
) -> list[NewsItem]:
    result = []
    for item in items:
        within = is_within_date_range(item.published_at, start, end)
        if within is True:
            result.append(item)
        elif within is None and keep_unparseable:
            result.append(item)
    return result
