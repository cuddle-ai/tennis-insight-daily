from jinja2 import Environment, FileSystemLoader
from src.data_sources.base import NewsItem


def render_daily_page(
    date: str,
    intro: str,
    items: list[NewsItem],
    template_dir: str = "templates",
    headlines_limit: int = 8,
    social_limit: int = 5,
) -> str:
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    tmpl = env.get_template("daily.html")

    headlines = [i for i in items if i.media_type == "article"][:headlines_limit]
    match_results = [i for i in items if i.media_type == "match_result"]
    schedules = [i for i in items if i.media_type == "schedule"]
    social_items = [
        i for i in items if i.media_type in ("video", "tweet", "instagram")
    ][:social_limit]
    player_news = [i for i in items if i.media_type == "article" and i not in headlines
                   and any(p for p in i.players)][:5]
    more_news = [i for i in items if i.media_type == "article"
                 and i not in headlines and i not in player_news]

    return tmpl.render(
        date=date,
        intro=intro,
        headlines=headlines,
        match_results=match_results,
        schedules=schedules,
        player_news=player_news,
        social_items=social_items,
        more_news=more_news,
    )
