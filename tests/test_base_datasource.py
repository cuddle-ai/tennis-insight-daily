# tests/test_base_datasource.py
import pytest
from src.data_sources.base import BaseDataSource, NewsItem

def test_news_item_required_fields():
    item = NewsItem(
        title="Sinner wins Roland Garros",
        url="https://example.com/article",
        source="Tennis.com",
        published_at="2026-05-11T06:00:00",
        media_type="article",
    )
    assert item.title == "Sinner wins Roland Garros"
    assert item.image_url is None
    assert item.summary is None

def test_base_datasource_is_abstract():
    with pytest.raises(TypeError):
        BaseDataSource()

def test_concrete_datasource_must_implement_fetch():
    class Incomplete(BaseDataSource):
        pass
    with pytest.raises(TypeError):
        Incomplete()
