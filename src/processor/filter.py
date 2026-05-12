from src.data_sources.base import NewsItem


def _player_keywords(players: list[str]) -> list[str]:
    """返回球员完整名和姓氏的集合，用于标题匹配"""
    keywords = set()
    for p in players:
        parts = p.lower().split()
        keywords.add(p.lower())  # 完整名
        if parts:
            keywords.add(parts[-1])  # 姓氏
    return list(keywords)


def filter_by_config(items: list[NewsItem], cfg: dict, section: str) -> list[NewsItem]:
    players = cfg.get(section, [])
    if not players:
        return items
    keywords = _player_keywords(players)
    return [
        item for item in items
        if any(kw in item.title.lower() for kw in keywords)
        or item.media_type in ("match_result", "schedule", "video", "tweet")
    ]
