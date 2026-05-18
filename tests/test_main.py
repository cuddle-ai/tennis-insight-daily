# tests/test_main.py
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch


def test_main_creates_output_file(tmp_path):
    from src.main import run_pipeline
    env = tmp_path / ".env"
    env.write_text("DEBUG_REPORT_ENABLED=false\n")
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.build_apify_instagram_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="今日导读。"), \
         patch("src.main.summarize_items", return_value=[]):
        run_pipeline(
            config_path=str(env),
            output_dir=str(tmp_path / "out"),
            template_dir="templates",
        )
    out = tmp_path / "out"
    files = list(out.glob("*.html"))
    assert any(f.name == "index.html" for f in files)
    daily_files = [f for f in files if f.name != "index.html"]
    assert len(daily_files) == 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert daily_files[0].name == f"{yesterday}.html"


def test_main_output_dir_is_created(tmp_path):
    from src.main import run_pipeline
    env = tmp_path / ".env"
    env.write_text("DEBUG_REPORT_ENABLED=false\n")
    new_dir = tmp_path / "output"
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.build_apify_instagram_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="导读。"), \
         patch("src.main.summarize_items", return_value=[]):
        run_pipeline(
            config_path=str(env),
            output_dir=str(new_dir),
            template_dir="templates",
        )
    assert new_dir.exists()
