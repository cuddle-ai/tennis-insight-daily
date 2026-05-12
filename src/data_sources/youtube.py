from googleapiclient.discovery import build
from .base import BaseDataSource, NewsItem


class YouTubeSource(BaseDataSource):
    def __init__(self, api_key: str, query: str, max_results: int = 3):
        self.api_key = api_key
        self.query = query
        self.max_results = max_results

    def fetch(self) -> list[NewsItem]:
        try:
            service = build("youtube", "v3", developerKey=self.api_key)
            response = (
                service.search()
                .list(q=self.query, part="snippet", type="video",
                      maxResults=self.max_results, order="date")
                .execute()
            )
            items = []
            for entry in response.get("items", []):
                video_id = entry["id"]["videoId"]
                snippet = entry["snippet"]
                embed_html = (
                    f'<iframe width="560" height="315" '
                    f'src="https://www.youtube.com/embed/{video_id}" '
                    f'frameborder="0" allowfullscreen></iframe>'
                )
                items.append(NewsItem(
                    title=snippet["title"],
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    source=snippet.get("channelTitle", "YouTube"),
                    published_at=snippet["publishedAt"],
                    media_type="video",
                    image_url=snippet["thumbnails"]["high"]["url"],
                    embed_html=embed_html,
                    weight=30,
                ))
            return items
        except Exception:
            return []


def build_youtube_source(cfg: dict) -> list[YouTubeSource]:
    if not cfg.get("sources", {}).get("youtube", True):
        return []
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        return []
    players = cfg.get("players", [])
    query = "tennis " + " OR ".join(players[:3]) if players else "tennis highlights"
    return [YouTubeSource(api_key=api_key, query=query, max_results=3)]
