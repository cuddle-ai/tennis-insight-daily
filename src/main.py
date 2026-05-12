import os
import anthropic
from datetime import date
from pathlib import Path

from src.config import load_config
from src.data_sources.rss_news import build_rss_sources
from src.data_sources.atp_wta import build_atp_wta_sources
from src.data_sources.youtube import build_youtube_source
from src.data_sources.twitter import build_twitter_source
from src.processor.dedup import dedup_items
from src.processor.filter import filter_by_config
from src.processor.sorter import assign_weights, sort_items
from src.processor.ai_summary import summarize_items, generate_daily_intro
from src.renderer.daily_page import render_daily_page
from src.renderer.index_page import render_index_page


def run_pipeline(
    config_path: str = "config.yaml",
    output_dir: str = "output",
    template_dir: str = "templates",
) -> None:
    cfg = load_config(config_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sources = (
        build_rss_sources(cfg)
        + build_atp_wta_sources(cfg)
        + build_youtube_source(cfg)
        + build_twitter_source(cfg)
    )
    all_items = []
    for source in sources:
        all_items.extend(source.fetch())

    all_items = dedup_items(all_items, threshold=0.8)
    all_items = filter_by_config(all_items, cfg, section="players")
    all_items = assign_weights(all_items, cfg)
    all_items = sort_items(all_items)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    ai_cfg = cfg.get("ai", {})
    model = ai_cfg.get("model", "claude-sonnet-4-6")
    language = ai_cfg.get("language", "zh")

    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        all_items = summarize_items(all_items, client=client, model=model, language=language)
        intro = generate_daily_intro(all_items, client=client, model=model, language=language)
    else:
        intro = "（AI 摘要未启用，请配置 ANTHROPIC_API_KEY）"

    today = date.today().isoformat()
    daily_html = render_daily_page(
        date=today, intro=intro, items=all_items, template_dir=template_dir
    )
    (out / f"{today}.html").write_text(daily_html, encoding="utf-8")

    existing_dates = sorted(
        [f.stem for f in out.glob("????-??-??.html")], reverse=True
    )
    index_html = render_index_page(dates=existing_dates, template_dir=template_dir)
    (out / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Done: output/{today}.html")


if __name__ == "__main__":
    run_pipeline()
