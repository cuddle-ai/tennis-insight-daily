# tests/test_main.py
import pytest
from unittest.mock import patch
from pathlib import Path

def test_main_creates_output_file(tmp_path):
    from src.main import run_pipeline
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="今日导读。"), \
         patch("src.main.summarize_items", return_value=[]):
        run_pipeline(
            config_path="config.yaml",
            output_dir=str(tmp_path),
            template_dir="templates",
        )
    files = list(tmp_path.glob("*.html"))
    assert any(f.name == "index.html" for f in files)
    daily_files = [f for f in files if f.name != "index.html"]
    assert len(daily_files) == 1

def test_main_output_dir_is_created(tmp_path):
    from src.main import run_pipeline
    new_dir = tmp_path / "output"
    with patch("src.main.build_rss_sources", return_value=[]), \
         patch("src.main.build_atp_wta_sources", return_value=[]), \
         patch("src.main.build_youtube_source", return_value=[]), \
         patch("src.main.build_twitter_source", return_value=[]), \
         patch("src.main.generate_daily_intro", return_value="导读。"), \
         patch("src.main.summarize_items", return_value=[]):
        run_pipeline(
            config_path="config.yaml",
            output_dir=str(new_dir),
            template_dir="templates",
        )
    assert new_dir.exists()
