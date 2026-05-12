from datetime import datetime, timedelta, timezone
from src.data_sources.base import NewsItem

GRAND_SLAMS = {"Roland Garros", "Wimbledon", "US Open", "Australian Open"}
MASTERS = {"Indian Wells", "Miami", "Monte Carlo", "Madrid", "Rome",
           "Canada", "Cincinnati", "Shanghai", "Paris"}


def _recency_bonus(published_at: str) -> int:
    """根据发布时间计算时效性加权：24h内+15，3天内+5"""
    try:
        raw = published_at
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        if delta < timedelta(hours=24):
            return 15
        if delta < timedelta(days=3):
            return 5
        return 0
    except Exception:
        return 0


def assign_weights(items: list[NewsItem], cfg: dict) -> list[NewsItem]:
    followed_players = {p.lower() for p in cfg.get("players", [])}
    followed_tournaments = {t.lower() for t in cfg.get("tournaments", [])}

    for item in items:
        w = item.weight

        if item.media_type == "match_result":
            item_tournaments = {t.lower() for t in item.tournaments}
            if item_tournaments & {t.lower() for t in GRAND_SLAMS}:
                w += 100
            elif item_tournaments & {t.lower() for t in MASTERS}:
                w += 60
            else:
                w += 40

        item_players = {p.lower() for p in item.players}
        if item_players & followed_players:
            w += 50

        title_lower = item.title.lower()
        if any(t.lower() in title_lower for t in followed_tournaments):
            w += 30
        if any(p.lower() in title_lower for p in followed_players):
            w += 20

        if item.media_type == "schedule":
            w += 35

        w += _recency_bonus(item.published_at)

        item.weight = w
    return items


def sort_items(items: list[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda i: i.weight, reverse=True)
