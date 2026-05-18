from datetime import date, datetime, timedelta, timezone

from src.data_sources.base import NewsItem
from src.time_utils import parse_datetime

GRAND_SLAMS = {"Roland Garros", "Wimbledon", "US Open", "Australian Open"}
MASTERS = {"Indian Wells", "Miami", "Monte Carlo", "Madrid", "Rome",
           "Canada", "Cincinnati", "Shanghai", "Paris"}


def _recency_bonus(published_at: str, target: date) -> int:
    """Bonus for items published later in the target day (afternoon > morning)."""
    dt = parse_datetime(published_at)
    if dt is None:
        return 0
    # Items published after 18:00 UTC on the target day get extra weight
    afternoon_cutoff = datetime(target.year, target.month, target.day, 18, tzinfo=timezone.utc)
    if dt >= afternoon_cutoff:
        return 10
    return 0


def assign_weights(items: list[NewsItem], cfg: dict, target: date | None = None) -> list[NewsItem]:
    if target is None:
        target = date.today() - timedelta(days=1)

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

        w += _recency_bonus(item.published_at, target)

        item.weight = w
    return items


def sort_items(items: list[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda i: i.weight, reverse=True)
