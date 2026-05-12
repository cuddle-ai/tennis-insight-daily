# tests/test_index_page.py
from src.renderer.index_page import render_index_page

def test_render_index_contains_date_links():
    html = render_index_page(
        dates=["2026-05-11", "2026-05-10", "2026-05-09"],
        template_dir="templates",
    )
    assert "2026-05-11" in html
    assert "2026-05-11.html" in html
    assert "2026-05-09" in html

def test_render_index_empty_dates():
    html = render_index_page(dates=[], template_dir="templates")
    assert "Tennis News Daily" in html
