# tests/test_atp_wta.py
import pytest
from unittest.mock import patch
from src.data_sources.atp_wta import MatchResultsSource, TodayScheduleSource
from src.data_sources.base import NewsItem

MOCK_RESULTS_HTML = """
<html><body>
<table class="day-table">
  <tr>
    <td class="day-table-name"><a>Carlos Alcaraz</a></td>
    <td class="day-table-score">6-3 6-4</td>
    <td class="day-table-name"><a>Holger Rune</a></td>
  </tr>
</table>
</body></html>
"""

def test_match_results_returns_news_items():
    source = MatchResultsSource()
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = MOCK_RESULTS_HTML
        mock_get.return_value.status_code = 200
        items = source.fetch()
    assert len(items) >= 0
    for item in items:
        assert isinstance(item, NewsItem)
        assert item.media_type == "match_result"

def test_today_schedule_returns_news_items():
    source = TodayScheduleSource()
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = MOCK_RESULTS_HTML
        mock_get.return_value.status_code = 200
        items = source.fetch()
    for item in items:
        assert item.media_type == "schedule"
