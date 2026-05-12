import requests
from bs4 import BeautifulSoup
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class InstagramSource(BaseDataSource):
    def __init__(self, username: str, max_posts: int = 3):
        self.username = username
        self.max_posts = max_posts

    def fetch(self) -> list[NewsItem]:
        try:
            url = f"https://www.instagram.com/{self.username}/"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")

            # 方案1：从 JSON-LD <script type="application/ld+json"> 提取
            items = self._parse_json_ld(soup, url)
            if items:
                return items[:self.max_posts]

            # 方案2：从 window._sharedData 提取
            return self._parse_shared_data(resp.text, url)[:self.max_posts]
        except Exception:
            return []

    def _parse_json_ld(self, soup: BeautifulSoup, account_url: str) -> list[NewsItem]:
        items = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            text = script.string or ""
            if '"@type":"SocialMediaPosting"' not in text:
                continue
            import json, re
            try:
                data = json.loads(text)
                post_url = data.get("url", "")
                headline = data.get("headline", "")
                image = data.get("image", "")
                date = data.get("datePublished", "")
                if post_url:
                    items.append(NewsItem(
                        title=headline[:100] or f"@{self.username} 最新帖子",
                        url=post_url,
                        source=f"@{self.username} (Instagram)",
                        published_at=date,
                        media_type="instagram",
                        image_url=image if isinstance(image, str) else None,
                        embed_html=self._embed_html(post_url),
                        weight=20,
                    ))
            except Exception:
                continue
        return items

    def _parse_shared_data(self, html: str, account_url: str) -> list[NewsItem]:
        items = []
        import json, re
        match = re.search(r'window\._sharedData\s*=\s*({.*?});\s*$', html, re.DOTALL)
        if not match:
            return items
        try:
            data = json.loads(match.group(1))
            entries = (
                data.get("entry_data", {})
                .get("ProfilePage", [{}])[0]
                .get("graphql", {})
                .get("user", {})
                .get("edge_owner_to_timeline_media", {})
                .get("edges", [])
            )
            for entry in entries:
                node = entry.get("node", {})
                shortcode = node.get("shortcode", "")
                post_url = f"https://www.instagram.com/p/{shortcode}/"
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = (
                    caption_edges[0].get("node", {}).get("text", "")
                    if caption_edges else ""
                )
                thumbnail = node.get("thumbnail_src") or node.get("display_url", "")
                date_ts = node.get("taken_at_timestamp", 0)
                from datetime import datetime
                published_at = (
                    datetime.utcfromtimestamp(date_ts).isoformat() + "Z"
                    if date_ts else ""
                )
                items.append(NewsItem(
                    title=caption[:100] or f"@{self.username} 最新帖子",
                    url=post_url,
                    source=f"@{self.username} (Instagram)",
                    published_at=published_at,
                    media_type="instagram",
                    image_url=thumbnail,
                    embed_html=self._embed_html(post_url),
                    weight=20,
                ))
        except Exception:
            pass
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


def build_instagram_source(cfg: dict) -> list[InstagramSource]:
    if not cfg.get("sources", {}).get("instagram", False):
        return []
    # 从 players 配置中补充球员 Instagram 账号
    player_mapping = {
        "Jannik Sinner": "sinner.official",
        "Carlos Alcaraz": "carlosalcaraz",
        "Zheng Qinwen": "qinfight",
    }
    accounts = list(INSTAGRAM_ACCOUNTS)
    for player in cfg.get("players", []):
        if player in player_mapping and player_mapping[player] not in accounts:
            accounts.append(player_mapping[player])

    return [InstagramSource(username=acct, max_posts=2) for acct in accounts]
