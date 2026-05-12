import os
import requests
from .base import BaseDataSource, NewsItem

INSTAGRAM_ACCOUNTS = [
    "atptour",
    "wtatennis",
    "rolandgarros",
    "wimbledon",
    "usopen",
    "australianopen",
    "sinner.official",
    "carlosalcaraz",
    "qinfight",
    "igau.swp",
    "sabalenko.aryna",
    "djokovic.nole",
]

APIFY_API_URL = "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"


class ApifyInstagramSource(BaseDataSource):
    """通过 Apify Instagram Scraper API 获取公开账号帖子"""

    def __init__(self, usernames: list[str], max_posts: int = 3):
        self.usernames = usernames
        self.max_posts = max_posts

    def fetch(self) -> list[NewsItem]:
        api_key = os.environ.get("APIFY_API_KEY", "")
        if not api_key:
            return []

        results = []
        for username in self.usernames[: self.max_posts]:
            items = self._fetch_account(username, api_key)
            results.extend(items)
            if len(results) >= self.max_posts:
                break
        return results[: self.max_posts]

    def _fetch_account(self, username: str, api_key: str) -> list[NewsItem]:
        try:
            payload = {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsLimit": 3,
            }
            resp = requests.post(
                APIFY_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if resp.status_code not in (200, 201):
                return []
            data = resp.json()
            # Apify sync endpoint returns dataset items directly as a list,
            # or wrapped in a dict with "data" key
            if isinstance(data, list):
                raw_items = data
            else:
                raw_items = data.get("data", []) or []
            return self._parse_items(raw_items, username)
        except Exception:
            return []

    def _parse_items(self, raw_items: list, username: str) -> list[NewsItem]:
        items = []
        for raw in raw_items:
            post_url = raw.get("url", "")
            caption = raw.get("caption", "") or raw.get("description", "")
            image = raw.get("displayUrl", "") or raw.get("thumbnailUrl", "")
            ts = raw.get("timestamp", "") or raw.get("createdAt", "")
            if not post_url:
                continue
            items.append(NewsItem(
                title=caption[:100] or f"@{username} 最新帖子",
                url=post_url,
                source=f"@{username} (Instagram)",
                published_at=ts,
                media_type="instagram",
                image_url=image if isinstance(image, str) else None,
                embed_html=self._embed_html(post_url),
                weight=20,
            ))
        return items

    def _embed_html(self, post_url: str) -> str:
        return (
            f'<blockquote class="instagram-media" '
            f'data-instgrm-permalink="{post_url}" '
            f'data-instgrm-version="14">'
            f'<a href="{post_url}">View this post on Instagram</a>'
            f'</blockquote>'
            f'<script async src="//www.instagram.com/embed.js"></script>'
        )


def build_apify_instagram_source(cfg: dict) -> list[ApifyInstagramSource]:
    if not cfg.get("sources", {}).get("instagram", False):
        return []
    player_mapping = {
        "Jannik Sinner": "sinner.official",
        "Carlos Alcaraz": "carlosalcaraz",
        "Zheng Qinwen": "qinfight",
    }
    accounts = list(INSTAGRAM_ACCOUNTS)
    for player in cfg.get("players", []):
        if player in player_mapping and player_mapping[player] not in accounts:
            accounts.append(player_mapping[player])
    return [ApifyInstagramSource(usernames=accounts, max_posts=3)]