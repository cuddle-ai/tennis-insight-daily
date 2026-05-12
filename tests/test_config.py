# tests/test_config.py
import pytest
from src.config import load_config

def test_load_config_returns_required_keys():
    cfg = load_config("config.yaml")
    assert "players" in cfg
    assert "tournaments" in cfg
    assert "sources" in cfg
    assert "ai" in cfg

def test_load_config_sources_has_flags():
    cfg = load_config("config.yaml")
    assert isinstance(cfg["sources"]["news"], bool)
    assert isinstance(cfg["sources"]["youtube"], bool)
    assert isinstance(cfg["sources"]["twitter"], bool)
    assert isinstance(cfg["sources"]["atp_wta"], bool)
