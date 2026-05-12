from datetime import datetime, timedelta, timezone
from src.data_sources.base import NewsItem


def filter_by_days(items: list[NewsItem], days: int = 3) -> list[NewsItem]:
    """
    过滤掉发布时间早于 N 天前的条目。
    解析失败的条目保留（不丢弃数据）。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for item in items:
        try:
            raw = item.published_at
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                result.append(item)
        except Exception:
            # 解析失败保留，避免丢失数据
            result.append(item)
    return result
