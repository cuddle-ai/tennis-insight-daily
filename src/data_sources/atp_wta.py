import requests
from datetime import date
from bs4 import BeautifulSoup
from .base import BaseDataSource, NewsItem

ATP_RESULTS_URL = "https://www.atptour.com/en/scores/results-archive"
ATP_SCHEDULE_URL = "https://www.atptour.com/en/scores/current"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TennisNewsDaily/1.0)"}


class MatchResultsSource(BaseDataSource):
    def fetch(self) -> list[NewsItem]:
        try:
            resp = requests.get(ATP_RESULTS_URL, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            for row in soup.select("table.day-table tr"):
                cells = row.select("td")
                if len(cells) < 3:
                    continue
                player1 = cells[0].get_text(strip=True)
                score = cells[1].get_text(strip=True)
                player2 = cells[2].get_text(strip=True)
                if not player1 or not score:
                    continue
                items.append(NewsItem(
                    title=f"{player1} def. {player2}  {score}",
                    url=ATP_RESULTS_URL,
                    source="ATP Tour",
                    published_at=date.today().isoformat(),
                    media_type="match_result",
                    players=[player1, player2],
                    weight=80,
                ))
            return items
        except Exception:
            return []


class TodayScheduleSource(BaseDataSource):
    def fetch(self) -> list[NewsItem]:
        try:
            resp = requests.get(ATP_SCHEDULE_URL, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            for row in soup.select("table.day-table tr"):
                cells = row.select("td")
                if len(cells) < 2:
                    continue
                player1 = cells[0].get_text(strip=True)
                player2 = cells[-1].get_text(strip=True)
                if not player1:
                    continue
                items.append(NewsItem(
                    title=f"今日赛程: {player1} vs {player2}",
                    url=ATP_SCHEDULE_URL,
                    source="ATP Tour",
                    published_at=date.today().isoformat(),
                    media_type="schedule",
                    players=[player1, player2],
                    weight=70,
                ))
            return items
        except Exception:
            return []


def build_atp_wta_sources(cfg: dict) -> list[BaseDataSource]:
    if not cfg.get("sources", {}).get("atp_wta", True):
        return []
    return [MatchResultsSource(), TodayScheduleSource()]
