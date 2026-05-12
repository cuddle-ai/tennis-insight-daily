from src.data_sources.base import NewsItem


def filter_by_config(items: list[NewsItem], cfg: dict, section: str) -> list[NewsItem]:
    keywords = [k.lower() for k in cfg.get(section, [])]
    if not keywords:
        return items
    return [
        item for item in items
        if any(kw in item.title.lower() for kw in keywords)
        or item.media_type in ("match_result", "schedule", "video", "tweet")
    ]
