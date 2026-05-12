# tests/test_processor.py
import pytest
from src.data_sources.base import NewsItem
from src.processor.dedup import dedup_items
from src.processor.filter import filter_by_config

def make_item(title, source="Tennis.com", media_type="article"):
    return NewsItem(title=title, url=f"https://example.com/{title}", source=source,
                    published_at="2026-05-11T06:00:00", media_type=media_type)

def test_dedup_removes_similar_titles():
    items = [
        make_item("Sinner wins Roland Garros final"),
        make_item("Sinner wins Roland Garros final match"),
        make_item("Alcaraz beats Rune in quarterfinal"),
    ]
    result = dedup_items(items, threshold=0.8)
    assert len(result) == 2

def test_dedup_keeps_dissimilar_items():
    items = [make_item("Sinner wins"), make_item("Alcaraz loses")]
    result = dedup_items(items, threshold=0.8)
    assert len(result) == 2

def test_filter_keeps_items_matching_players():
    cfg = {"players": ["Sinner"], "tournaments": []}
    items = [
        make_item("Sinner wins Roland Garros"),
        make_item("Alcaraz beats Rune"),
    ]
    result = filter_by_config(items, cfg, section="players")
    assert any("Sinner" in i.title for i in result)

def test_filter_returns_all_when_no_config():
    cfg = {"players": [], "tournaments": []}
    items = [make_item("Any news"), make_item("Other news")]
    result = filter_by_config(items, cfg, section="players")
    assert len(result) == 2
