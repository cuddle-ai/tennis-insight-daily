import os

import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from time import perf_counter

from src.config import load_config
from src.data_sources.apify_instagram import build_apify_instagram_source
from src.data_sources.atp_wta import build_atp_wta_sources
from src.data_sources.rss_news import build_rss_sources
from src.data_sources.twitter import build_twitter_source
from src.data_sources.youtube import build_youtube_source
from src.debug_report import (
    render_debug_report,
    serialize_items,
    summarize_items as summarize_trace_items,
    trace_dedup,
    trace_render_partition,
    trace_date_range,
)
from src.processor.ai_summary import generate_daily_intro, summarize_items
from src.processor.filter import filter_by_config
from src.processor.sorter import assign_weights, sort_items
from src.renderer.daily_page import render_daily_page
from src.renderer.index_page import render_index_page
from src.time_utils import CST, filter_by_date_range, get_target_date_range


def _fetch_source_items(source) -> dict:
    started = perf_counter()
    try:
        items = source.fetch()
        return {
            "name": type(source).__name__,
            "status": "ok",
            "duration_seconds": round(perf_counter() - started, 2),
            "error": "",
            "items": serialize_items(items),
            "raw_items": items,
            "summary": summarize_trace_items(items),
            "diagnostics": getattr(source, "last_diagnostics", []),
        }
    except Exception as exc:
        return {
            "name": type(source).__name__,
            "status": "error",
            "duration_seconds": round(perf_counter() - started, 2),
            "error": str(exc),
            "items": [],
            "raw_items": [],
            "summary": summarize_trace_items([]),
            "diagnostics": [],
        }


def run_pipeline(
    config_path: str = ".env",
    output_dir: str = "output",
    template_dir: str = "templates",
) -> None:
    cfg = load_config(config_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    debug_enabled = cfg.get("debug", {}).get("report_enabled", False)

    # T-1: target date defaults to yesterday (CST), override via TARGET_DATE env
    env_target = os.environ.get("TARGET_DATE", "").strip()
    if env_target:
        target_date = date.fromisoformat(env_target)
    else:
        target_date = (datetime.now(CST) - timedelta(days=1)).date()
    start_utc, end_utc = get_target_date_range(target_date)

    sources = (
        build_rss_sources(cfg)
        + build_atp_wta_sources(cfg)
        + build_youtube_source(cfg)
        + build_twitter_source(cfg)
        + build_apify_instagram_source(cfg)
    )
    source_traces = []
    all_items = []
    max_workers = min(len(sources), 8) or 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_fetch_source_items, source) for source in sources]
        for future in as_completed(futures):
            source_trace = future.result()
            source_traces.append(source_trace)
            all_items.extend(source_trace["raw_items"])

    stage_traces = []
    deduped_items, dedup_removed = trace_dedup(all_items, threshold=0.8)
    stage_traces.append(
        {
            "name": "去重",
            "description": "按标题相似度阈值 0.8 去除近似重复条目。",
            "input_summary": summarize_trace_items(all_items),
            "output_summary": summarize_trace_items(deduped_items),
            "input_items": serialize_items(all_items),
            "output_items": serialize_items(deduped_items),
            "removed": dedup_removed,
            "since": "",
        }
    )

    filtered_items = filter_by_config(deduped_items, cfg, section="players")
    stage_traces.append(
        {
            "name": "偏好过滤",
            "description": "当前不过滤条目，players 和 tournaments 仅作为排序偏好信号。",
            "input_summary": summarize_trace_items(deduped_items),
            "output_summary": summarize_trace_items(filtered_items),
            "input_items": serialize_items(deduped_items),
            "output_items": serialize_items(filtered_items),
            "removed": [],
            "since": "",
        }
    )

    # T-1 date-range filter: only keep items from target_date
    date_range_items, date_range_removed, range_label = trace_date_range(
        filtered_items,
        start=start_utc,
        end=end_utc,
    )
    stage_traces.append(
        {
            "name": "日期范围",
            "description": f"仅保留目标日期 {target_date.isoformat()} 的条目；无法解析时间的条目默认保留。",
            "input_summary": summarize_trace_items(filtered_items),
            "output_summary": summarize_trace_items(date_range_items),
            "input_items": serialize_items(filtered_items),
            "output_items": serialize_items(date_range_items),
            "removed": date_range_removed,
            "since": range_label,
        }
    )

    weighted_items = assign_weights(date_range_items, cfg)
    all_items = sort_items(weighted_items)
    stage_traces.append(
        {
            "name": "排序",
            "description": "应用偏好权重和时效权重后，按权重从高到低排序。",
            "input_summary": summarize_trace_items(date_range_items),
            "output_summary": summarize_trace_items(all_items),
            "input_items": serialize_items(date_range_items),
            "output_items": serialize_items(all_items),
            "removed": [],
            "since": "",
        }
    )

    api_key = cfg.get("ai", {}).get("api_key", "")
    ai_cfg = cfg.get("ai", {})
    model = ai_cfg.get("model", "qwen3.6-plus")
    base_url = ai_cfg.get("base_url", "")
    language = ai_cfg.get("language", "zh")

    if api_key:
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = openai.OpenAI(**kwargs)
        try:
            all_items = summarize_items(all_items, client=client, model=model, language=language)
            intro = generate_daily_intro(all_items, client=client, model=model, language=language)
        except Exception as exc:
            print(f"AI 摘要生成失败: {exc}")
            intro = "（AI 摘要生成失败，已保留原始内容）"
    else:
        intro = "（AI 摘要未启用，请配置 api_key）"

    target_str = target_date.isoformat()
    render_trace = trace_render_partition(
        all_items,
        headlines_limit=cfg.get("content", {}).get("headlines_limit", 8),
        social_limit=cfg.get("content", {}).get("social_limit", 5),
    )
    daily_html = render_daily_page(
        date=target_str,
        intro=intro,
        items=all_items,
        template_dir=template_dir,
        headlines_limit=cfg.get("content", {}).get("headlines_limit", 8),
        social_limit=cfg.get("content", {}).get("social_limit", 5),
    )
    (out / f"{target_str}.html").write_text(daily_html, encoding="utf-8")

    if debug_enabled:
        debug_path = out / f"{target_str}-debug.html"
        debug_html = render_debug_report(
            date=target_str,
            config_path=config_path,
            debug_meta={
                "数据源数量": len(sources),
                "采集条目数": sum(trace["summary"]["count"] for trace in source_traces),
                "最终条目数": len(all_items),
                "AI 已启用": "是" if bool(api_key) else "否",
                "目标日期": target_str,
                "头条上限": cfg.get("content", {}).get("headlines_limit", 8),
                "社交精选上限": cfg.get("content", {}).get("social_limit", 5),
            },
            source_traces=sorted(source_traces, key=lambda trace: trace["name"]),
            stage_traces=stage_traces,
            render_trace=render_trace,
            output_path=str(debug_path),
            template_dir=template_dir,
        )
        debug_path.write_text(debug_html, encoding="utf-8")

    existing_dates = sorted([f.stem for f in out.glob("????-??-??.html")], reverse=True)
    index_html = render_index_page(dates=existing_dates, template_dir=template_dir)
    (out / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Done: output/{target_str}.html")
    if debug_enabled:
        print(f"Debug: output/{target_str}-debug.html")


if __name__ == "__main__":
    run_pipeline()
