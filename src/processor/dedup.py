from difflib import SequenceMatcher
from src.data_sources.base import NewsItem


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def dedup_items(items: list[NewsItem], threshold: float = 0.8) -> list[NewsItem]:
    kept = []
    for item in items:
        if not any(_similarity(item.title, k.title) >= threshold for k in kept):
            kept.append(item)
    return kept
