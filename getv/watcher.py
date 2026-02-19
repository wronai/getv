"""File watcher — auto-reload .env profiles on change.

Uses polling (cross-platform) with optional inotify acceleration on Linux.

Usage::

    from getv.watcher import EnvWatcher

    def on_change(category, profile, store):
        print(f"Reloaded: {category}/{profile}")

    watcher = EnvWatcher("~/.getv", on_change=on_change)
    watcher.start()   # background thread
    # ... later ...
    watcher.stop()

Or as a context manager::

    with EnvWatcher("~/.getv", on_change=on_change):
        # profiles auto-reload while this block runs
        ...
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from getv.store import EnvStore


class EnvWatcher:
    """Watch .env profiles for changes and call back on modification.

    Args:
        base_dir: getv home directory (e.g. ~/.getv).
        on_change: Callback ``(category: str, profile: str, store: EnvStore) -> None``.
        interval: Polling interval in seconds.
    """

    def __init__(
        self,
        base_dir: str = "~/.getv",
        on_change: Optional[Callable[[str, str, EnvStore], None]] = None,
        interval: float = 2.0,
    ) -> None:
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.on_change = on_change
        self.interval = interval
        self._mtimes: Dict[Path, float] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _scan(self) -> Dict[Path, Tuple[str, str]]:
        """Scan for all .env files and return {path: (category, profile)}."""
        result: Dict[Path, Tuple[str, str]] = {}
        if not self.base_dir.exists():
            return result
        for cat_dir in sorted(self.base_dir.iterdir()):
            if not cat_dir.is_dir() or cat_dir.name.startswith("."):
                continue
            for env_file in sorted(cat_dir.glob("*.env")):
                result[env_file] = (cat_dir.name, env_file.stem)
        return result

    def _check_once(self) -> int:
        """Check for changed files. Returns number of changes detected."""
        changes = 0
        files = self._scan()

        for path, (category, profile) in files.items():
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue

            old_mtime = self._mtimes.get(path)
            self._mtimes[path] = mtime

            if old_mtime is not None and mtime != old_mtime:
                changes += 1
                if self.on_change:
                    try:
                        store = EnvStore(path, auto_create=False)
                        self.on_change(category, profile, store)
                    except Exception:
                        pass

        # Detect deleted files
        deleted = set(self._mtimes) - set(files)
        for path in deleted:
            del self._mtimes[path]

        return changes

    def _run(self) -> None:
        """Background polling loop."""
        # Initial scan to populate mtimes (no callbacks on first scan)
        self._scan_initial()
        while not self._stop.is_set():
            self._check_once()
            self._stop.wait(self.interval)

    def _scan_initial(self) -> None:
        """Populate mtimes without triggering callbacks."""
        files = self._scan()
        for path in files:
            try:
                self._mtimes[path] = path.stat().st_mtime
            except OSError:
                pass

    def start(self) -> None:
        """Start watching in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="getv-watcher")
        self._thread.start()

    def stop(self) -> None:
        """Stop the watcher."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def check(self) -> int:
        """Manual one-shot check (no background thread needed). Returns change count."""
        if not self._mtimes:
            self._scan_initial()
        return self._check_once()

    @property
    def watching(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def __enter__(self) -> "EnvWatcher":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()

    def __repr__(self) -> str:
        status = "watching" if self.watching else "stopped"
        return f"EnvWatcher({self.base_dir}, {status}, {len(self._mtimes)} files)"
