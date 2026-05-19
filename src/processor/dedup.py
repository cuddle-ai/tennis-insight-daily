from __future__ import annotations

import json
from collections import defaultdict
from difflib import SequenceMatcher

import openai

from src.data_sources.base import NewsItem

_DEDUP_PROMPT = """\
你是网球新闻去重助手。给定同一数据源的一组新闻标题，找出描述同一事件的标题，将它们分为同一组。

判断规则：
- 核心事件相同即为重复。例如同一场比赛结果、同一项赛事赛程、同一球员的同一新闻，无论语言、详略、措辞差异
- 不同角度不算重复。例如"辛纳夺冠"和"辛纳夺冠后的排名变化"是不同事件
- 同一球员的不同赛事不算重复
- 拿不准的不要合并

标题列表：
{titles}

返回 JSON，格式为分组数组。每组是一个标题编号列表，第一个编号为保留的标题（优先选信息最完整的）。不在任何组中的标题视为独立条目，无需列出。

示例输出：
[[1, 3, 7], [2, 5]]

表示标题 1/3/7 描述同一事件（保留 1），标题 2/5 描述同一事件（保留 2），其余标题独立保留。"""


def _build_numbered_titles(items: list[NewsItem]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item.title}")
    return "\n".join(lines)


def _parse_groups(raw: str, count: int) -> list[list[int]]:
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
    groups = json.loads(text)
    valid: list[list[int]] = []
    seen: set[int] = set()
    for group in groups:
        if not isinstance(group, list) or len(group) < 2:
            continue
        ints = [n for n in group if isinstance(n, int) and 1 <= n <= count and n not in seen]
        if len(ints) >= 2:
            valid.append(ints)
            seen.update(ints)
    return valid


def _group_by_source(items: list[NewsItem]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, item in enumerate(items):
        groups[item.source].append(i)
    return groups


def ai_dedup(
    items: list[NewsItem],
    client: openai.OpenAI,
    model: str,
    batch_size: int = 50,
) -> list[NewsItem]:
    if not items:
        return []

    source_groups = _group_by_source(items)
    dup_indices: set[int] = set()

    for source, indices in source_groups.items():
        offset = 0
        while offset < len(indices):
            batch_indices = indices[offset : offset + batch_size]
            batch_items = [items[i] for i in batch_indices]
            titles_text = _build_numbered_titles(batch_items)
            prompt = _DEDUP_PROMPT.format(titles=titles_text)

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = resp.choices[0].message.content or "[]"
            groups = _parse_groups(raw, len(batch_items))

            for group in groups:
                group_items = [batch_items[n - 1] for n in group]
                best = max(group_items, key=lambda x: x.weight)
                for n in group:
                    idx = batch_indices[n - 1]
                    if items[idx] is not best:
                        dup_indices.add(idx)

            offset += batch_size

    return [item for i, item in enumerate(items) if i not in dup_indices]


def dedup_items(items: list[NewsItem], threshold: float = 0.8) -> list[NewsItem]:
    source_groups = _group_by_source(items)
    kept_indices: set[int] = set()

    for source, indices in source_groups.items():
        kept: list[int] = []
        for idx in indices:
            if not any(_similarity(items[idx].title, items[k].title) >= threshold for k in kept):
                kept.append(idx)
        kept_indices.update(kept)

    return [items[i] for i in sorted(kept_indices)]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
