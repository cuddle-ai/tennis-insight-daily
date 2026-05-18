import re
import time
from datetime import datetime, timedelta, timezone
from .base import BaseDataSource, NewsItem

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

PLAYER_USERNAME_MAP = {
    "Jannik Sinner": "JannikSinner",
    "Carlos Alcaraz": "carlitosalcaraz",
    "Zheng Qinwen": "qinfight",
    "Aryna Sabalenka": "SabalenkaA",
    "Iga Swiatek": "igawojtek",
    "Novak Djokovic": "NovakD",
    "Rafael Nadal": "RafaelNadal",
}

_MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _parse_twitter_date(date_str: str) -> datetime | None:
    """Parse Twitter date strings. Returns None if unparseable."""
    try:
        now = datetime.now(timezone.utc)
        date_str = date_str.strip()

        m = re.match(r'^(\d+)h$', date_str)
        if m:
            return now - timedelta(hours=int(m.group(1)))
        m = re.match(r'^(\d+)m$', date_str)
        if m:
            return now - timedelta(minutes=int(m.group(1)))
        m = re.match(r'^(\d+)s$', date_str)
        if m:
            return now - timedelta(seconds=int(m.group(1)))
        m = re.match(r'^(\d+)d$', date_str)
        if m:
            return now - timedelta(days=int(m.group(1)))

        m = re.match(r'^([A-Za-z]{3})\s+(\d{1,2})$', date_str)
        if m:
            month = _MONTH_MAP.get(m.group(1))
            day = int(m.group(2))
            if month:
                return datetime(now.year, month, day, tzinfo=timezone.utc)

        m = re.match(r'^([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{4})$', date_str)
        if m:
            month = _MONTH_MAP.get(m.group(1))
            day = int(m.group(2))
            year = int(m.group(3))
            if month:
                return datetime(year, month, day, tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _extract_date_from_text(text: str) -> datetime | None:
    """从推文文本中提取日期作为备选"""
    # 尝试匹配 "May 12" 或 "May 12, 2025" 格式
    for pattern in [
        r'([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{4})',
        r'([A-Za-z]{3})\s+(\d{1,2})(?:\s|$)',
    ]:
        m = re.search(pattern, text)
        if m:
            dt = _parse_twitter_date(m.group(0))
            if dt:
                return dt
    return None


# JavaScript to extract tweets from x.com profile page via Playwright
_SCRAPE_JS = (
    "() => {"
    "var SEP = String.fromCharCode(10);"
    "var MID = String.fromCharCode(183);"
    "var results = [];"
    "var articles = document.querySelectorAll('article');"
    "for (var ai = 0; ai < Math.min(articles.length, 5); ai++) {"
    "  var el = articles[ai];"
    "  var links = el.querySelectorAll('a');"
    "  var tweetUrl = '';"
    "  for (var li = 0; li < links.length; li++) {"
    "    var href = links[li].href || '';"
    "    if (href.indexOf('/status/') >= 0) { tweetUrl = href; break; }"
    "  }"
    "  var lines = (el.innerText || '').split(SEP);"
    "  var timeStr = '', textParts = [], inText = false;"
    "  for (var li = 0; li < lines.length; li++) {"
    "    var l = lines[li].trim();"
    "    if (!l) continue;"
    "    if (l.indexOf(MID) >= 0) {"
    "      if (l.length === 1 && l === MID) { inText = true; continue; }"
    "      var parts = l.split(MID);"
    "      for (var pi = 0; pi < parts.length; pi++) {"
    "        var part = parts[pi].trim();"
    "        if (!part) continue;"
    "        if (!timeStr) { timeStr = part; inText = true; }"
    "        else if (inText && part) textParts.push(part);"
    "      }"
    "      continue;"
    "    }"
    "    if (inText && l) textParts.push(l);"
    "  }"
    "  var text = textParts.join(' ').trim();"
    "  if (text.length > 5) results.push({url: tweetUrl, timeStr: timeStr, text: text.substring(0, 200)});"
    "}"
    "return results;"
    "}"
)


def _scrape_twitter_page(username: str) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    tweets = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(15000)

            response = page.goto(f"https://x.com/{username}", timeout=15000)
            if not response or response.status != 200:
                browser.close()
                return []

            page.wait_for_load_state("domcontentloaded", timeout=8000)
            time.sleep(3)

            raw_articles = page.evaluate(_SCRAPE_JS)
            tweets = raw_articles if raw_articles else []
            browser.close()
    except Exception:
        pass
    return tweets


class TwitterSource(BaseDataSource):
    def __init__(self, usernames: list[str], max_results: int = 10, since_days: int = 3):
        self.usernames = usernames
        self.max_results = max_results
        self.since_days = since_days

    def fetch(self) -> list[NewsItem]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.since_days)
        all_items = []

        for username in self.usernames:
            if len(all_items) >= self.max_results:
                break

            raw_tweets = _scrape_twitter_page(username)
            for tweet in raw_tweets:
                tweet_url = tweet.get("url", "") or f"https://x.com/{username}"

                # 优先从 timeStr 解析，其次从文本中提取
                dt = _parse_twitter_date(tweet.get("timeStr", ""))
                if dt is None:
                    dt = _extract_date_from_text(tweet.get("text", ""))

                # 无法确定时间则跳过（不默认当前时间，避免久远内容绕过时效过滤）
                if dt is None:
                    continue
                if dt < cutoff:
                    continue

                published_at = dt.isoformat()

                embed_html = (
                    '<blockquote class="twitter-tweet">'
                    f'<a href="{tweet_url}"></a>'
                    '</blockquote>'
                    '<script async src="https://platform.twitter.com/widgets.js"></script>'
                )
                all_items.append(NewsItem(
                    title=tweet["text"][:100],
                    url=tweet_url,
                    source=f"@{username}",
                    published_at=published_at,
                    media_type="tweet",
                    embed_html=embed_html,
                    weight=20,
                ))
                if len(all_items) >= self.max_results:
                    break

        return all_items


def _build_twitter_usernames(players: list[str]) -> list[str]:
    usernames = list(OFFICIAL_ACCOUNTS)
    for player in players:
        username = PLAYER_USERNAME_MAP.get(player)
        if username and username not in usernames:
            usernames.append(username)
    return usernames


def build_twitter_source(cfg: dict) -> list[TwitterSource]:
    if not cfg.get("sources", {}).get("twitter", True):
        return []
    players = cfg.get("players", [])
    usernames = _build_twitter_usernames(players)
    return [TwitterSource(usernames=usernames, max_results=10, since_days=2)]