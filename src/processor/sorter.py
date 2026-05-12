from src.data_sources.base import NewsItem

GRAND_SLAMS = {"Roland Garros", "Wimbledon", "US Open", "Australian Open"}
MASTERS = {"Indian Wells", "Miami", "Monte Carlo", "Madrid", "Rome",
           "Canada", "Cincinnati", "Shanghai", "Paris"}


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

        item.weight = w
    return items


def sort_items(items: list[NewsItem]) -> list[NewsItem]:
    return sorted(items, key=lambda i: i.weight, reverse=True)
