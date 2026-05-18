from src.data_sources.base import NewsItem
from src.debug_report import trace_dedup, trace_render_partition, trace_date_range


def make_item(
    title: str,
    media_type: str = "article",
    published_at: str = "2026-05-13T10:00:00+00:00",
    weight: int = 0,
):
    return NewsItem(
        title=title,
        url=f"https://example.com/{title}",
        source="Test",
        published_at=published_at,
        media_type=media_type,
        weight=weight,
    )


def test_trace_dedup_reports_removed_items():
    kept, removed = trace_dedup(
        [make_item("Sinner wins Rome"), make_item("Sinner wins Rome match")],
        threshold=0.8,
    )
    assert len(kept) == 1
    assert len(removed) == 1
    assert removed[0]["reason"] == "标题相似去重"


def test_trace_date_range_reports_old_items():
    kept, removed, range_label = trace_date_range(
        [
            make_item("on-date", published_at="2026-05-13T10:00:00+00:00"),
            make_item("off-date", published_at="2026-05-11T10:00:00+00:00"),
        ],
        start=__import__("datetime").datetime(2026, 5, 13, tzinfo=__import__("datetime").timezone.utc),
        end=__import__("datetime").datetime(2026, 5, 14, tzinfo=__import__("datetime").timezone.utc),
    )
    assert len(kept) == 1
    assert len(removed) == 1
    assert "超出目标日期范围" in removed[0]["reason"]
    assert range_label


def test_trace_render_partition_reports_social_limit_exceeded():
    items = [
        make_item("video-1", media_type="video"),
        make_item("video-2", media_type="video"),
        make_item("video-3", media_type="video"),
    ]
    render_trace = trace_render_partition(items, headlines_limit=8, social_limit=2)
    assert render_trace["counts"]["社交精选"] == 2
    assert len(render_trace["excluded"]) == 1
    assert render_trace["excluded"][0]["reason"] == "社交精选上限截断"
