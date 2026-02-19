"""Tests for ProfileManager validation, diff, copy features."""

import pytest
from pathlib import Path

from getv.profile import ProfileManager, ProfileValidationError


@pytest.fixture
def pm(tmp_path):
    """ProfileManager with test categories."""
    p = ProfileManager(tmp_path)
    p.add_category("llm", required_keys=["LLM_MODEL", "API_KEY"])
    p.add_category("devices", required_keys=["HOST", "USER"])
    return p


class TestValidation:

    def test_validate_ok(self, pm):
        missing = pm.validate("llm", {"LLM_MODEL": "groq/llama3", "API_KEY": "gsk_xxx"})
        assert missing == []

    def test_validate_missing_keys(self, pm):
        missing = pm.validate("llm", {"LLM_MODEL": "groq/llama3"})
        assert missing == ["API_KEY"]

    def test_validate_empty_value_counts_as_missing(self, pm):
        missing = pm.validate("llm", {"LLM_MODEL": "groq/llama3", "API_KEY": ""})
        assert missing == ["API_KEY"]

    def test_validate_all_missing(self, pm):
        missing = pm.validate("llm", {"EXTRA": "val"})
        assert sorted(missing) == ["API_KEY", "LLM_MODEL"]

    def test_validate_unregistered_category(self, pm):
        # Unregistered category has no required_keys → always valid
        missing = pm.validate("unknown", {"anything": "ok"})
        assert missing == []

    def test_set_with_validate_ok(self, pm):
        store = pm.set("llm", "groq", {"LLM_MODEL": "llama3", "API_KEY": "gsk_x"}, validate=True)
        assert store.get("LLM_MODEL") == "llama3"

    def test_set_with_validate_raises(self, pm):
        with pytest.raises(ProfileValidationError) as exc_info:
            pm.set("llm", "groq", {"LLM_MODEL": "llama3"}, validate=True)
        err = exc_info.value
        assert err.category == "llm"
        assert err.name == "groq"
        assert err.missing == ["API_KEY"]

    def test_set_without_validate_allows_incomplete(self, pm):
        # Default: no validation
        store = pm.set("llm", "groq", {"LLM_MODEL": "llama3"})
        assert store.get("LLM_MODEL") == "llama3"


class TestDiff:

    def test_diff_identical(self, pm):
        pm.set("llm", "a", {"LLM_MODEL": "gpt-4", "API_KEY": "sk-123"})
        pm.set("llm", "b", {"LLM_MODEL": "gpt-4", "API_KEY": "sk-123"})
        assert pm.diff("llm", "a", "b") == {}

    def test_diff_changed_value(self, pm):
        pm.set("llm", "a", {"LLM_MODEL": "gpt-4", "API_KEY": "sk-111"})
        pm.set("llm", "b", {"LLM_MODEL": "gpt-4", "API_KEY": "sk-222"})
        d = pm.diff("llm", "a", "b")
        assert "API_KEY" in d
        assert d["API_KEY"] == ("sk-111", "sk-222")
        assert "LLM_MODEL" not in d

    def test_diff_added_key(self, pm):
        pm.set("llm", "a", {"LLM_MODEL": "gpt-4"})
        pm.set("llm", "b", {"LLM_MODEL": "gpt-4", "EXTRA": "val"})
        d = pm.diff("llm", "a", "b")
        assert d["EXTRA"] == (None, "val")

    def test_diff_removed_key(self, pm):
        pm.set("llm", "a", {"LLM_MODEL": "gpt-4", "OLD": "val"})
        pm.set("llm", "b", {"LLM_MODEL": "gpt-4"})
        d = pm.diff("llm", "a", "b")
        assert d["OLD"] == ("val", None)

    def test_diff_multiple_changes(self, pm):
        pm.set("llm", "a", {"A": "1", "B": "2", "C": "3"})
        pm.set("llm", "b", {"A": "1", "B": "X", "D": "4"})
        d = pm.diff("llm", "a", "b")
        assert "A" not in d  # same
        assert d["B"] == ("2", "X")  # changed
        assert d["C"] == ("3", None)  # removed
        assert d["D"] == (None, "4")  # added

    def test_diff_nonexistent_profile(self, pm):
        pm.set("llm", "a", {"X": "1"})
        # b doesn't exist → empty dict → all keys show as removed
        d = pm.diff("llm", "a", "nonexistent")
        assert d["X"] == ("1", None)


class TestCopy:

    def test_copy_same_category(self, pm):
        pm.set("llm", "groq", {"LLM_MODEL": "llama3", "API_KEY": "gsk_x"})
        store = pm.copy("llm", "groq", "llm", "groq-backup")
        assert store.get("LLM_MODEL") == "llama3"
        assert store.get("API_KEY") == "gsk_x"
        # Both profiles exist
        assert pm.exists("llm", "groq")
        assert pm.exists("llm", "groq-backup")

    def test_copy_cross_category(self, pm):
        pm.set("llm", "groq", {"LLM_MODEL": "llama3", "API_KEY": "gsk_x"})
        store = pm.copy("llm", "groq", "api", "groq")
        assert store.get("LLM_MODEL") == "llama3"
        assert pm.exists("api", "groq")

    def test_copy_overwrites_destination(self, pm):
        pm.set("llm", "a", {"X": "1"})
        pm.set("llm", "b", {"Y": "2"})
        pm.copy("llm", "a", "llm", "b")
        data = pm.get_dict("llm", "b")
        assert data.get("X") == "1"

    def test_copy_nonexistent_source_raises(self, pm):
        with pytest.raises(FileNotFoundError):
            pm.copy("llm", "nonexistent", "llm", "backup")
