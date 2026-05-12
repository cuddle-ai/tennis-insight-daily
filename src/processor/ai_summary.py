import openai
from src.data_sources.base import NewsItem


def summarize_items(
    items: list[NewsItem],
    client: openai.OpenAI,
    model: str,
    language: str = "zh",
) -> list[NewsItem]:
    lang_name = "中文" if language == "zh" else "English"
    for item in items:
        if item.media_type not in ("article",):
            continue
        if not item.summary:
            continue
        prompt = (
            f"请用{lang_name}将以下网球新闻摘要压缩为2-3句话，简洁客观，适合早间快读。\n\n"
            f"标题：{item.title}\n原文摘要：{item.summary}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        item.summary = response.choices[0].message.content.strip()
    return items


def generate_daily_intro(
    items: list[NewsItem],
    client: openai.OpenAI,
    model: str,
    language: str = "zh",
) -> str:
    lang_name = "中文" if language == "zh" else "English"
    headlines = "\n".join(f"- {i.title}" for i in items[:10])
    prompt = (
        f"以下是今日网球资讯标题列表，请用{lang_name}写一段3-5句的今日导读，"
        f"概括最重要的事件，语气简洁、客观。\n\n{headlines}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
