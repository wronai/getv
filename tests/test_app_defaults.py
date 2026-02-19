"""Tests for getv.app_defaults — per-app default profile selection."""

import pytest
from pathlib import Path
from getv.app_defaults import AppDefaults


@pytest.fixture
def tmp_getv(tmp_path):
    """Create a temporary getv directory."""
    return str(tmp_path)


class TestAppDefaults:
    def test_set_and_get(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        assert d.get("llm") == "groq"

    def test_get_default(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        assert d.get("llm") is None
        assert d.get("llm", "fallback") == "fallback"

    def test_persistence(self, tmp_getv):
        d1 = AppDefaults("myapp", base_dir=tmp_getv)
        d1.set("llm", "groq")
        d1.set("devices", "rpi3")

        d2 = AppDefaults("myapp", base_dir=tmp_getv)
        assert d2.get("llm") == "groq"
        assert d2.get("devices") == "rpi3"

    def test_remove(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        d.remove("llm")
        assert d.get("llm") is None

    def test_as_dict(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        d.set("devices", "rpi3")
        assert d.as_dict() == {"llm": "groq", "devices": "rpi3"}

    def test_as_profile_kwargs(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        kwargs = d.as_profile_kwargs()
        assert kwargs == {"llm": "groq"}

    def test_list_apps(self, tmp_getv):
        AppDefaults("app1", base_dir=tmp_getv).set("llm", "a")
        AppDefaults("app2", base_dir=tmp_getv).set("llm", "b")
        apps = AppDefaults.list_apps(base_dir=tmp_getv)
        assert "app1" in apps
        assert "app2" in apps

    def test_list_apps_empty(self, tmp_getv):
        assert AppDefaults.list_apps(base_dir=tmp_getv) == []

    def test_multiple_apps_isolated(self, tmp_getv):
        AppDefaults("app1", base_dir=tmp_getv).set("llm", "groq")
        AppDefaults("app2", base_dir=tmp_getv).set("llm", "ollama")
        assert AppDefaults("app1", base_dir=tmp_getv).get("llm") == "groq"
        assert AppDefaults("app2", base_dir=tmp_getv).get("llm") == "ollama"

    def test_overwrite(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        d.set("llm", "openrouter")
        assert d.get("llm") == "openrouter"

    def test_repr(self, tmp_getv):
        d = AppDefaults("myapp", base_dir=tmp_getv)
        d.set("llm", "groq")
        r = repr(d)
        assert "myapp" in r
        assert "groq" in r
