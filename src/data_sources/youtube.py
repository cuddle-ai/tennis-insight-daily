from googleapiclient.discovery import build
from .base import BaseDataSource, NewsItem

# YouTube 频道 ID（官方网球组织，已验证）
CHANNEL_IDS = {
    "atptour":         "UCY_5h5zaSwN7Or4kIJDYNXA",
    "wtatennis":       "UCaBIVVpHjq6j3tSyxwTE-8Q",
    "tennischannel":   "UCDitdIjOjS9Myza9I21IqzQ",
    "rolandgarros":    "UCF3K1Jf8hjFW8qliei8fQ3A",
    "wimbledon":        "UCNa8NxMgSm7m4Ii9d4QGk1Q",
    "usopen":          "UCXbboag48Qlr78zzz6SkzkQ",
    "australianopen":  "UCeTKJSW1NTAkf27nNmjWt5A",
}

# 球员频道 ID（优先使用）
PLAYER_CHANNEL_IDS = {
    "Jannik Sinner":   "UC921lTfUVbGqHcfL4rtRhqQ",
    "Carlos Alcaraz":  "UC26T_YGKJaqfDE_nPxckF0w",
    # Zheng Qinwen 无官方频道，使用 WTA 频道覆盖
}


class YouTubeSource(BaseDataSource):
    def __init__(self, api_key: str, channel_ids: list[str], max_results: int = 3):
        self.api_key = api_key
        self.channel_ids = channel_ids
        self.max_results = max_results

    def fetch(self) -> list[NewsItem]:
        try:
            service = build("youtube", "v3", developerKey=self.api_key)
        except Exception:
            return []

        all_items = []
        for channel_id in self.channel_ids:
            try:
                response = (
                    service.search()
                    .list(
                        q="tennis",
                        channelId=channel_id,
                        part="snippet",
                        type="video",
                        maxResults=self.max_results,
                        order="date",
                    )
                    .execute()
                )
            except Exception:
                continue

            for entry in response.get("items", []):
                video_id = entry["id"]["videoId"]
                snippet = entry["snippet"]
                embed_html = (
                    f'<iframe width="560" height="315" '
                    f'src="https://www.youtube.com/embed/{video_id}" '
                    f'frameborder="0" allowfullscreen></iframe>'
                )
                all_items.append(NewsItem(
                    title=snippet["title"],
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    source=snippet.get("channelTitle", "YouTube"),
                    published_at=snippet["publishedAt"],
                    media_type="video",
                    image_url=snippet["thumbnails"]["high"]["url"],
                    embed_html=embed_html,
                    weight=30,
                ))

        return all_items[: self.max_results]


def build_youtube_source(cfg: dict) -> list[YouTubeSource]:
    if not cfg.get("sources", {}).get("youtube", True):
        return []
    api_key = cfg.get("youtube", {}).get("api_key", "")
    if not api_key:
        return []

    # 优先使用配置的球员频道 ID，其次使用球员名称搜索
    channel_ids = list(CHANNEL_IDS.values())
    for player in cfg.get("players", []):
        if player in PLAYER_CHANNEL_IDS:
            cid = PLAYER_CHANNEL_IDS[player]
            if cid not in channel_ids:
                channel_ids.append(cid)

    return [YouTubeSource(api_key=api_key, channel_ids=channel_ids, max_results=3)]
