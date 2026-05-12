# tests/test_renderer.py
import pytest
from src.data_sources.base import NewsItem
from src.renderer.daily_page import render_daily_page

def make_article(title):
    return NewsItem(
        title=title, url="https://example.com", source="Tennis.com",
        published_at="2026-05-11T06:00:00", media_type="article",
        summary="AI 生成的摘要。", image_url="https://example.com/img.jpg",
    )

def make_video():
    return NewsItem(
        title="Roland Garros Highlights", url="https://youtube.com/watch?v=abc",
        source="Tennis TV", published_at="2026-05-11T05:00:00", media_type="video",
        embed_html='<iframe src="https://www.youtube.com/embed/abc"></iframe>',
    )

def test_render_daily_page_contains_date():
    html = render_daily_page(
        date="2026-05-11", intro="今日导读内容。",
        items=[make_article("Sinner wins")], template_dir="templates",
    )
    assert "2026-05-11" in html

def test_render_daily_page_contains_article_title():
    html = render_daily_page(
        date="2026-05-11", intro="导读。",
        items=[make_article("Sinner wins Roland Garros")], template_dir="templates",
    )
    assert "Sinner wins Roland Garros" in html

def test_render_daily_page_embeds_video():
    html = render_daily_page(
        date="2026-05-11", intro="导读。",
        items=[make_video()], template_dir="templates",
    )
    assert "youtube.com/embed/abc" in html
