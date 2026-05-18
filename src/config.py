import os
from pathlib import Path


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def load_config(path: str = ".env") -> dict:
    env_values = _parse_dotenv(Path(path))
    merged = {**env_values, **os.environ}

    return {
        "players": _parse_list(merged.get("PLAYERS")),
        "tournaments": _parse_list(merged.get("TOURNAMENTS")),
        "sources": {
            "news": _parse_bool(merged.get("SOURCES_NEWS"), True),
            "atp_wta": _parse_bool(merged.get("SOURCES_ATP_WTA"), True),
            "youtube": _parse_bool(merged.get("SOURCES_YOUTUBE"), True),
            "twitter": _parse_bool(merged.get("SOURCES_TWITTER"), True),
            "instagram": _parse_bool(merged.get("SOURCES_INSTAGRAM"), True),
        },
        "content": {
            "headlines_limit": _parse_int(
                merged.get("CONTENT_HEADLINES_LIMIT"),
                8,
            ),
            "social_limit": _parse_int(
                merged.get("CONTENT_SOCIAL_LIMIT"),
                5,
            ),
        },
        "ai": {
            "model": merged.get("AI_MODEL", "qwen3.6-max-preview"),
            "base_url": merged.get("AI_BASE_URL", ""),
            "api_key": merged.get("AI_API_KEY") or merged.get("DASHSCOPE_API_KEY", ""),
            "language": merged.get("AI_LANGUAGE", "zh"),
        },
        "youtube": {
            "api_key": merged.get("YOUTUBE_API_KEY", ""),
        },
        "apify": {
            "api_key": merged.get("APIFY_API_KEY", ""),
        },
        "schedule": {
            "publish_time": merged.get("SCHEDULE_PUBLISH_TIME", "07:00"),
        },
        "debug": {
            "report_enabled": _parse_bool(merged.get("DEBUG_REPORT_ENABLED"), False),
        },
    }
