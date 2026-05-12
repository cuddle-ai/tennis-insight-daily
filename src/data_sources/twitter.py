from .base import BaseDataSource, NewsItem


class TwitterSource(BaseDataSource):
    def __init__(self, query: str, max_results: int = 3):
        self.query = query
        self.max_results = max_results

    def fetch(self) -> list[NewsItem]:
        try:
            import snscrape.modules.twitter as sntwitter
            scraper = sntwitter.TwitterSearchScraper(self.query)
            items = []
            for i, tweet in enumerate(scraper.get_items()):
                if i >= self.max_results:
                    break
                embed_html = (
                    f'<blockquote class="twitter-tweet">'
                    f'<a href="https://twitter.com/{tweet.user.username}/status/{tweet.id}"></a>'
                    f'</blockquote>'
                    f'<script async src="https://platform.twitter.com/widgets.js"></script>'
                )
                items.append(NewsItem(
                    title=tweet.rawContent[:100],
                    url=f"https://twitter.com/{tweet.user.username}/status/{tweet.id}",
                    source=f"@{tweet.user.username}",
                    published_at=tweet.date.isoformat(),
                    media_type="tweet",
                    embed_html=embed_html,
                    weight=20,
                ))
            return items
        except Exception:
            return []


def build_twitter_source(cfg: dict) -> list[TwitterSource]:
    if not cfg.get("sources", {}).get("twitter", True):
        return []
    players = cfg.get("players", [])
    query = "tennis (" + " OR ".join(players[:3]) + ")" if players else "tennis -filter:retweets"
    return [TwitterSource(query=query, max_results=3)]
