# tests/test_config.py
import pytest
from src.config import load_config


def test_load_config_from_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "PLAYERS=Sinner,Alcaraz\n"
        "TOURNAMENTS=Roland Garros\n"
        "SOURCES_NEWS=true\n"
        "SOURCES_YOUTUBE=false\n"
        "AI_MODEL=qwen3.6-max-preview\n"
    )
    cfg = load_config(str(env))
    assert "Sinner" in cfg["players"]
    assert "Roland Garros" in cfg["tournaments"]
    assert cfg["sources"]["news"] is True
    assert cfg["sources"]["youtube"] is False


def test_load_config_returns_required_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text("")
    cfg = load_config(str(env))
    assert "players" in cfg
    assert "tournaments" in cfg
    assert "sources" in cfg
    assert "ai" in cfg
    assert "content" in cfg


def test_load_config_sources_has_flags(tmp_path):
    env = tmp_path / ".env"
    env.write_text("")
    cfg = load_config(str(env))
    assert isinstance(cfg["sources"]["news"], bool)
    assert isinstance(cfg["sources"]["youtube"], bool)
    assert isinstance(cfg["sources"]["twitter"], bool)
    assert isinstance(cfg["sources"]["atp_wta"], bool)
