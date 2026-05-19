import json
import pytest
from unittest.mock import MagicMock

from src.data_sources.base import NewsItem
from src.processor.dedup import ai_dedup, dedup_items
from src.processor.filter import filter_by_config

def make_item(title, source="Tennis.com", media_type="article", weight=0):
    return NewsItem(title=title, url=f"https://example.com/{title}", source=source,
                    published_at="2026-05-11T06:00:00", media_type=media_type, weight=weight)

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

def test_dedup_keeps_same_title_different_source():
    items = [
        make_item("Sinner wins Rome Masters", source="BBC"),
        make_item("Sinner wins Rome Masters", source="ESPN"),
    ]
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


# --- AI dedup tests ---

def _mock_client(response_text: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = response_text
    client = MagicMock()
    client.chat.completions.create.return_value = mock_resp
    return client


def test_ai_dedup_groups_same_source():
    items = [
        make_item("Sinner wins Rome Masters title", source="BBC", weight=10),
        make_item("辛纳罗马大师赛夺冠", source="BBC", weight=5),
        make_item("Alcaraz advances to semifinal", source="BBC", weight=8),
    ]
    client = _mock_client("[[1, 2]]")
    result = ai_dedup(items, client=client, model="test")
    assert len(result) == 2
    assert result[0].title == "Sinner wins Rome Masters title"
    assert result[1].title == "Alcaraz advances to semifinal"


def test_ai_dedup_keeps_same_event_different_source():
    items = [
        make_item("Sinner wins Rome Masters", source="BBC", weight=10),
        make_item("辛纳罗马大师赛夺冠", source="ESPN", weight=5),
    ]
    client = _mock_client("[[1, 2]]")
    result = ai_dedup(items, client=client, model="test")
    assert len(result) == 2


def test_ai_dedup_keeps_higher_weight():
    items = [
        make_item("Sinner wins Rome Masters title", source="BBC", weight=5),
        make_item("辛纳罗马大师赛夺冠", source="BBC", weight=10),
    ]
    client = _mock_client("[[1, 2]]")
    result = ai_dedup(items, client=client, model="test")
    assert len(result) == 1
    assert result[0].title == "辛纳罗马大师赛夺冠"


def test_ai_dedup_no_duplicates():
    items = [
        make_item("Sinner wins Rome Masters"),
        make_item("Alcaraz wins Monte Carlo"),
    ]
    client = _mock_client("[]")
    result = ai_dedup(items, client=client, model="test")
    assert len(result) == 2


def test_ai_dedup_empty_list():
    client = _mock_client("[]")
    result = ai_dedup([], client=client, model="test")
    assert result == []


def test_ai_dedup_fallback_on_parse_error():
    items = [
        make_item("Sinner wins"),
        make_item("Alcaraz wins"),
    ]
    client = _mock_client("not valid json")
    with pytest.raises(json.JSONDecodeError):
        ai_dedup(items, client=client, model="test")
