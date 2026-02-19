"""Tests for getv.profile.ProfileManager."""

import pytest
from pathlib import Path
from getv.profile import ProfileManager


@pytest.fixture
def pm(tmp_path):
    """Create a ProfileManager with temp base dir."""
    manager = ProfileManager(tmp_path)
    manager.add_category("devices", required_keys=["RPI_HOST", "RPI_USER"])
    manager.add_category("llm", required_keys=["LLM_MODEL"])
    return manager


def test_set_and_get(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "192.168.1.10", "RPI_USER": "pi", "RPI_PORT": "22"})
    store = pm.get("devices", "rpi3")
    assert store is not None
    assert store.get("RPI_HOST") == "192.168.1.10"
    assert store.get("RPI_USER") == "pi"


def test_get_dict(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "10.0.0.1"})
    d = pm.get_dict("devices", "rpi3")
    assert d["RPI_HOST"] == "10.0.0.1"


def test_get_nonexistent(pm):
    assert pm.get("devices", "nonexistent") is None
    assert pm.get_dict("devices", "nonexistent") == {}


def test_delete(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "x"})
    assert pm.exists("devices", "rpi3")
    assert pm.delete("devices", "rpi3") is True
    assert pm.exists("devices", "rpi3") is False
    assert pm.delete("devices", "rpi3") is False


def test_list(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "a"})
    pm.set("devices", "rpi4", {"RPI_HOST": "b"})
    profiles = pm.list("devices")
    names = [name for name, _ in profiles]
    assert "rpi3" in names
    assert "rpi4" in names


def test_list_names(pm):
    pm.set("llm", "groq", {"LLM_MODEL": "groq/llama3"})
    pm.set("llm", "openrouter", {"LLM_MODEL": "openrouter/gemini"})
    assert sorted(pm.list_names("llm")) == ["groq", "openrouter"]


def test_list_categories(pm):
    cats = pm.list_categories()
    assert "devices" in cats
    assert "llm" in cats


def test_merge_profiles(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "10.0.0.1", "RPI_USER": "pi"})
    pm.set("llm", "groq", {"LLM_MODEL": "groq/llama3", "GROQ_API_KEY": "gsk_xxx"})

    base = {"APP_NAME": "fixpi", "RPI_HOST": "default"}
    merged = pm.merge_profiles(base, devices="rpi3", llm="groq")
    assert merged["APP_NAME"] == "fixpi"
    assert merged["RPI_HOST"] == "10.0.0.1"  # overridden by device profile
    assert merged["LLM_MODEL"] == "groq/llama3"
    assert merged["GROQ_API_KEY"] == "gsk_xxx"


def test_merge_profiles_none_skipped(pm):
    base = {"KEY": "val"}
    merged = pm.merge_profiles(base, devices=None, llm=None)
    assert merged == {"KEY": "val"}


def test_find_by_key(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "192.168.1.10"})
    pm.set("devices", "rpi4", {"RPI_HOST": "192.168.1.20"})
    pm.set("devices", "rpi5", {"RPI_HOST": "192.168.1.10"})

    matches = pm.find_by_key("devices", "RPI_HOST", "192.168.1.10")
    assert sorted(matches) == ["rpi3", "rpi5"]


def test_list_table(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret123"})
    rows = pm.list_table("devices")
    assert len(rows) == 1
    assert rows[0]["name"] == "rpi3"
    assert rows[0]["RPI_HOST"] == "10.0.0.1"
    assert "secret123" not in rows[0]["RPI_PASSWORD"]  # masked


def test_list_all(pm):
    pm.set("devices", "rpi3", {"RPI_HOST": "a"})
    pm.set("llm", "groq", {"LLM_MODEL": "b"})
    all_data = pm.list_all()
    assert "devices" in all_data
    assert "llm" in all_data
    assert len(all_data["devices"]) == 1
    assert len(all_data["llm"]) == 1
