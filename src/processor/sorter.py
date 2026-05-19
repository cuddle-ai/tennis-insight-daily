from datetime import date, datetime, timedelta, timezone

from src.data_sources.base import NewsItem
from src.time_utils import parse_datetime

GRAND_SLAMS = {"Roland Garros", "Wimbledon", "US Open", "Australian Open"}
MASTERS = {"Indian Wells", "Miami", "Monte Carlo", "Madrid", "Rome",
           "Canada", "Cincinnati", "Shanghai", "Paris"}


def _recency_bonus(published_at: str, target: date) -> int:
    dt = parse_datetime(published_at)
    if dt is None:
        return 0
    afternoon_cutoff = datetime(target.year, target.month, target.day, 18, tzinfo=timezone.utc)
    if dt >= afternoon_cutoff:
        return 10
    return 0


def _player_tokens(players: list[str]) -> set[str]:
    tokens = set()
    for name in players:
        for part in name.lower().split():
            if len(part) > 2:
                tokens.add(part)
    return tokens


def _tournament_aliases(tournaments: list[str]) -> set[str]:
    aliases = set()
    for t in tournaments:
        aliases.add(t.lower())
    # common aliases
    mapping = {
        "roland garros": {"french open", "法网"},
        "wimbledon": {"温网"},
        "us open": {"美网", "flushing meadows"},
        "australian open": {"澳网", "melbourne"},
    }
    for t in tournaments:
        for alias in mapping.get(t.lower(), ()):
            aliases.add(alias)
    return aliases


def assign_weights(items: list[NewsItem], cfg: dict, target: date | None = None) -> list[NewsItem]:
    if target is None:
        target = date.today() - timedelta(days=1)

    followed_players = {p.lower() for p in cfg.get("players", [])}
    player_tokens = _player_tokens(cfg.get("players", []))
    tournament_aliases = _tournament_aliases(cfg.get("tournaments", []))

    for item in items:
        w = item.weight

        # media type bonus
        if item.media_type == "match_result":
            item_tournaments = {t.lower() for t in item.tournaments}
            if item_tournaments & {t.lower() for t in GRAND_SLAMS}:
                w += 100
            elif item_tournaments & {t.lower() for t in MASTERS}:
                w += 60
            else:
                w += 40

        if item.media_type == "schedule":
            w += 35

        # followed players/tournaments from item metadata
        item_players = {p.lower() for p in item.players}
        if item_players & followed_players:
            w += 50

        # followed players/tournaments from title text
        title_lower = item.title.lower()
        if any(alias in title_lower for alias in tournament_aliases):
            w += 30
        if any(token in title_lower for token in player_tokens):
            w += 20

        w += _recency_bonus(item.published_at, target)

        item.weight = w
    return items


def sort_items(items: list[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda i: i.weight, reverse=True)
