# tests/test_sorter.py
from datetime import date

from src.data_sources.base import NewsItem
from src.processor.sorter import sort_items, assign_weights


def make_item(title, media_type="article", players=None, tournaments=None, weight=0, published_at="2026-05-17T06:00:00+00:00"):
    return NewsItem(
        title=title, url="https://example.com", source="Tennis.com",
        published_at=published_at, media_type=media_type,
        players=players or [], tournaments=tournaments or [], weight=weight,
    )


def test_assign_weights_grand_slam_result():
    cfg = {"players": ["Sinner"], "tournaments": ["Roland Garros"]}
    item = make_item("Sinner wins Roland Garros", media_type="match_result",
                     players=["Sinner"], tournaments=["Roland Garros"])
    result = assign_weights([item], cfg, target=date(2026, 5, 17))
    assert result[0].weight >= 100


def test_assign_weights_followed_player():
    cfg = {"players": ["Sinner"], "tournaments": []}
    item = make_item("Sinner press conference", players=["Sinner"])
    result = assign_weights([item], cfg, target=date(2026, 5, 17))
    assert result[0].weight >= 50


def test_sort_items_orders_by_weight_descending():
    items = [
        make_item("Low priority", weight=10),
        make_item("High priority", weight=100),
        make_item("Medium priority", weight=50),
    ]
    result = sort_items(items)
    assert result[0].weight == 100
    assert result[1].weight == 50
    assert result[2].weight == 10
