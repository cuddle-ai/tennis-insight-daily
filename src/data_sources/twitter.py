from datetime import datetime, timedelta, timezone
from .base import BaseDataSource, NewsItem

# 官方网球组织账号
OFFICIAL_ACCOUNTS = [
    "atptour",
    "WTA",
    "ITFtennis",
    "TennisChannel",
    "rolandgarros",
    "Wimbledon",
    "AustralianOpen",
    "usopen",
]


class TwitterSource(BaseDataSource):
    def __init__(self, query: str, max_results: int = 10, since_days: int = 3):
        self.query = query
        self.max_results = max_results
        self.since_days = since_days

    def fetch(self) -> list[NewsItem]:
        try:
            import snscrape.modules.twitter as sntwitter
            scraper = sntwitter.TwitterSearchScraper(self.query)
            items = []
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.since_days)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= self.max_results:
                    break
                try:
                    tweet_dt = tweet.date
                    if tweet_dt.tzinfo is None:
                        tweet_dt = tweet_dt.replace(tzinfo=timezone.utc)
                    if tweet_dt < cutoff:
                        continue
                except Exception:
                    pass

                embed_html = (
                    f'<blockquote class="twitter-tweet">'
                    f'<a href="https://twitter.com/{tweet.user.username}/status/{tweet.id}"></a>'
                    f'</blockquote>'
                    f'<script async src="https://platform.twitter.com/widgets.js"></script>'
                )
                published_at = tweet_dt.isoformat()
                items.append(NewsItem(
                    title=tweet.rawContent[:100],
                    url=f"https://twitter.com/{tweet.user.username}/status/{tweet.id}",
                    source=f"@{tweet.user.username}",
                    published_at=published_at,
                    media_type="tweet",
                    embed_html=embed_html,
                    weight=20,
                ))
            return items
        except Exception:
            return []


def _build_twitter_query(players: list[str]) -> str:
    parts = [f"from:{acct}" for acct in OFFICIAL_ACCOUNTS]

    player_accounts = [
        "JannikSinner",
        "carlitosalcaraz",
        "qinfight",
        "SabalenkaA",
        "igawojtek",
        "imkeMaeland",
        "NovakD",
        "RafaelNadal",
    ]
    for name, username in [(p, _name_to_username(p)) for p in players]:
        if username:
            player_accounts.append(username)
    parts.extend(f"from:{acct}" for acct in player_accounts)

    return " OR ".join(parts)


def _name_to_username(name: str) -> str | None:
    mapping = {
        "Jannik Sinner": "JannikSinner",
        "Carlos Alcaraz": "carlitosalcaraz",
        "Zheng Qinwen": "qinfight",
        "Aryna Sabalenka": "SabalenkaA",
        "Iga Swiatek": "igawojtek",
        "Novak Djokovic": "NovakD",
        "Rafael Nadal": "RafaelNadal",
    }
    return mapping.get(name)


def build_twitter_source(cfg: dict) -> list[TwitterSource]:
    if not cfg.get("sources", {}).get("twitter", True):
        return []
    players = cfg.get("players", [])
    recency_days = cfg.get("content", {}).get("recency_days", 3)
    query = _build_twitter_query(players)
    return [TwitterSource(query=query, max_results=10, since_days=recency_days)]
