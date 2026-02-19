"""Tests for getv.watcher — file watching / auto-reload."""

import time
import pytest
from pathlib import Path

from getv.watcher import EnvWatcher
from getv.profile import ProfileManager


@pytest.fixture
def pm(tmp_path):
    p = ProfileManager(tmp_path)
    p.add_category("llm")
    p.set("llm", "groq", {"LLM_MODEL": "llama3", "API_KEY": "gsk_test"})
    return p


class TestEnvWatcher:

    def test_initial_scan(self, tmp_path, pm):
        w = EnvWatcher(str(tmp_path))
        w._scan_initial()
        assert len(w._mtimes) == 1

    def test_check_no_changes(self, tmp_path, pm):
        w = EnvWatcher(str(tmp_path))
        w._scan_initial()
        assert w.check() == 0

    def test_check_detects_modification(self, tmp_path, pm):
        changes = []

        def on_change(cat, prof, store):
            changes.append((cat, prof, store.as_dict()))

        w = EnvWatcher(str(tmp_path), on_change=on_change)
        w._scan_initial()

        # Modify the file
        env_file = tmp_path / "llm" / "groq.env"
        time.sleep(0.05)  # ensure mtime differs
        env_file.write_text("LLM_MODEL=gpt-4\nAPI_KEY=sk_new\n")
        # Force mtime change (some filesystems have 1s resolution)
        import os
        os.utime(env_file, (time.time() + 1, time.time() + 1))

        count = w.check()
        assert count == 1
        assert len(changes) == 1
        assert changes[0][0] == "llm"
        assert changes[0][1] == "groq"
        assert changes[0][2]["LLM_MODEL"] == "gpt-4"

    def test_check_detects_new_file(self, tmp_path, pm):
        changes = []
        w = EnvWatcher(str(tmp_path), on_change=lambda c, p, s: changes.append((c, p)))
        w._scan_initial()

        # Add new profile
        pm.set("llm", "openai", {"LLM_MODEL": "gpt-4"})
        # New files won't trigger callback on first detection (no old mtime)
        count = w.check()
        # First detection registers mtime but no callback
        assert count == 0
        assert len(w._mtimes) == 2

    def test_check_detects_deleted_file(self, tmp_path, pm):
        w = EnvWatcher(str(tmp_path))
        w._scan_initial()
        assert len(w._mtimes) == 1

        # Delete profile
        (tmp_path / "llm" / "groq.env").unlink()
        w.check()
        assert len(w._mtimes) == 0

    def test_start_stop(self, tmp_path, pm):
        w = EnvWatcher(str(tmp_path), interval=0.1)
        assert not w.watching
        w.start()
        assert w.watching
        w.stop()
        assert not w.watching

    def test_context_manager(self, tmp_path, pm):
        with EnvWatcher(str(tmp_path), interval=0.1) as w:
            assert w.watching
        assert not w.watching

    def test_repr(self, tmp_path, pm):
        w = EnvWatcher(str(tmp_path))
        assert "stopped" in repr(w)
        assert "EnvWatcher" in repr(w)

    def test_empty_dir(self, tmp_path):
        w = EnvWatcher(str(tmp_path))
        w._scan_initial()
        assert len(w._mtimes) == 0
        assert w.check() == 0

    def test_callback_exception_doesnt_crash(self, tmp_path, pm):
        """on_change raising an exception should not crash the watcher."""
        def bad_callback(cat, prof, store):
            raise RuntimeError("boom")

        w = EnvWatcher(str(tmp_path), on_change=bad_callback)
        w._scan_initial()

        env_file = tmp_path / "llm" / "groq.env"
        import os
        os.utime(env_file, (time.time() + 1, time.time() + 1))

        # Should not raise
        count = w.check()
        assert count == 1
