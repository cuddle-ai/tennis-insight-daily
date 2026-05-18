from datetime import date, timedelta

from src.data_sources.base import NewsItem
from src.time_utils import filter_by_date_range, get_target_date_range


def filter_by_target_date(items: list[NewsItem], target: date | None = None) -> list[NewsItem]:
    """Filter items to only include those from the target calendar date (T-1 by default)."""
    start, end = get_target_date_range(target)
    return filter_by_date_range(items, start, end)
