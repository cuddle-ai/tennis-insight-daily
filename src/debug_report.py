from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.data_sources.base import NewsItem
from src.time_utils import get_target_date_range, is_within_date_range, parse_datetime


def item_key(item: NewsItem) -> str:
    return "|".join([item.title, item.url, item.source, item.published_at, item.media_type])


def serialize_item(item: NewsItem) -> dict[str, Any]:
    data = asdict(item)
    data["key"] = item_key(item)
    return data


def serialize_items(items: list[NewsItem]) -> list[dict[str, Any]]:
    return [serialize_item(item) for item in items]


def summarize_items(items: list[NewsItem]) -> dict[str, Any]:
    return {
        "count": len(items),
        "media_types": dict(Counter(item.media_type for item in items)),
    }


def trace_dedup(items: list[NewsItem], threshold: float) -> tuple[list[NewsItem], list[dict[str, Any]]]:
    kept: list[NewsItem] = []
    removed: list[dict[str, Any]] = []
    for item in items:
        duplicate_of = None
        similarity = 0.0
        for kept_item in kept:
            score = SequenceMatcher(None, item.title.lower(), kept_item.title.lower()).ratio()
            if score >= threshold:
                duplicate_of = kept_item
                similarity = score
                break
        if duplicate_of is None:
            kept.append(item)
            continue
        removed.append(
            {
                "item": serialize_item(item),
                "reason": "标题相似去重",
                "duplicate_of": serialize_item(duplicate_of),
                "similarity": round(similarity, 3),
            }
        )
    return kept, removed


def trace_date_range(
    items: list[NewsItem],
    start: datetime,
    end: datetime,
) -> tuple[list[NewsItem], list[dict[str, Any]], str]:
    kept: list[NewsItem] = []
    removed: list[dict[str, Any]] = []
    for item in items:
        within = is_within_date_range(item.published_at, start, end)
        if within is True or within is None:
            kept.append(item)
            continue
        parsed = parse_datetime(item.published_at)
        removed.append(
            {
                "item": serialize_item(item),
                "reason": f"超出目标日期范围 [{start.date()}]",
                "since": start.isoformat(),
                "published_at_parsed": parsed.isoformat() if parsed else item.published_at,
            }
        )
    return kept, removed, f"{start.date()} ~ {end.date()}"


def trace_render_partition(
    items: list[NewsItem],
    headlines_limit: int,
    social_limit: int,
) -> dict[str, Any]:
    headlines = [i for i in items if i.media_type == "article"][:headlines_limit]
    match_results = [i for i in items if i.media_type == "match_result"]
    schedules = [i for i in items if i.media_type == "schedule"]
    social_candidates = [i for i in items if i.media_type in ("video", "tweet", "instagram")]
    social_items = social_candidates[:social_limit]
    player_news = [
        i for i in items
        if i.media_type == "article" and i not in headlines and any(p for p in i.players)
    ][:5]
    more_news = [
        i for i in items
        if i.media_type == "article" and i not in headlines and i not in player_news
    ]

    shown_keys: set[str] = set()
    partitions = {
        "头条新闻": headlines,
        "赛事结果": match_results,
        "赛程": schedules,
        "球员动态": player_news,
        "社交精选": social_items,
        "更多新闻": more_news,
    }
    for section_items in partitions.values():
        for item in section_items:
            shown_keys.add(item_key(item))

    social_shown_keys = {item_key(item) for item in social_items}
    excluded: list[dict[str, Any]] = []
    for item in items:
        key = item_key(item)
        if key in shown_keys:
            continue
        reason = "未进入最终页面"
        if item.media_type in ("video", "tweet", "instagram") and key not in social_shown_keys:
            reason = "社交精选上限截断"
        excluded.append({"item": serialize_item(item), "reason": reason})

    return {
        "partitions": {
            name: serialize_items(section_items)
            for name, section_items in partitions.items()
        },
        "counts": {name: len(section_items) for name, section_items in partitions.items()},
        "excluded": excluded,
    }


def render_debug_report(
    *,
    date: str,
    config_path: str,
    debug_meta: dict[str, Any],
    source_traces: list[dict[str, Any]],
    stage_traces: list[dict[str, Any]],
    render_trace: dict[str, Any],
    output_path: str,
    template_dir: str = "templates",
) -> str:
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    tmpl = env.get_template("debug_report.html")
    return tmpl.render(
        generated_at=datetime.now(timezone.utc).isoformat(),
        date=date,
        config_path=config_path,
        debug_meta=debug_meta,
        source_traces=source_traces,
        stage_traces=stage_traces,
        render_trace=render_trace,
        output_path=output_path,
    )
