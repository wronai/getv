"""EnvStore — core read/write/list/delete for .env files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


class EnvStore:
    """
    Manages key=value pairs in a single .env file.

    Preserves comments and blank lines on save.  Thread-safe for
    single-process use (no file locking across processes).

    Usage::

        store = EnvStore("~/.fixpi/devices/rpi3.env")
        store.set("RPI_HOST", "192.168.1.100")
        store.save()

        host = store.get("RPI_HOST")
        all_vars = store.as_dict()
    """

    def __init__(self, path: str | Path, auto_create: bool = True) -> None:
        self.path = Path(path).expanduser().resolve()
        self._data: Dict[str, str] = {}
        self._raw_lines: List[str] = []
        self._loaded = False

        if self.path.exists():
            self._load()
        elif auto_create:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    # ── Read ─────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Parse .env file, extracting key=value pairs."""
        self._raw_lines = self.path.read_text(encoding="utf-8").splitlines()
        self._data.clear()
        for line in self._raw_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            self._data[key] = value
        self._loaded = True

    def reload(self) -> "EnvStore":
        """Re-read from disk."""
        if self.path.exists():
            self._load()
        return self

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a variable value."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def items(self) -> List[Tuple[str, str]]:
        return list(self._data.items())

    def as_dict(self) -> Dict[str, str]:
        """Return all variables as a plain dict."""
        return dict(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    # ── Write ────────────────────────────────────────────────────────────

    def set(self, key: str, value: str) -> "EnvStore":
        """Set a variable (in memory). Call save() to persist."""
        self._data[key] = value
        return self

    def update(self, mapping: Dict[str, str]) -> "EnvStore":
        """Bulk-set from a dict."""
        self._data.update(mapping)
        return self

    def delete(self, key: str) -> "EnvStore":
        """Remove a variable."""
        self._data.pop(key, None)
        return self

    def save(self) -> Path:
        """
        Write to disk, preserving comments from the original file.
        New keys are appended at the end.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)

        written_keys: set = set()
        new_lines: List[str] = []

        for line in self._raw_lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                new_lines.append(line)
                continue
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in self._data:
                    new_lines.append(f"{key}={self._data[key]}")
                    written_keys.add(key)
                elif key not in self._data:
                    # Key was deleted — skip line
                    continue
            else:
                new_lines.append(line)

        # Append new keys not in original
        for key, value in self._data.items():
            if key not in written_keys:
                new_lines.append(f"{key}={value}")

        self.path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        self._raw_lines = new_lines
        return self.path

    # ── Merge / overlay ──────────────────────────────────────────────────

    def merge_from(self, other: "EnvStore") -> "EnvStore":
        """Overlay another store's values on top of this one."""
        self._data.update(other._data)
        return self

    def merge_file(self, path: str | Path) -> "EnvStore":
        """Overlay values from another .env file."""
        other = EnvStore(path, auto_create=False)
        return self.merge_from(other)

    # ── Export ────────────────────────────────────────────────────────────

    def to_shell_export(self) -> str:
        """Generate shell export statements."""
        lines = []
        for key, value in sorted(self._data.items()):
            escaped = value.replace("'", "'\\''")
            lines.append(f"export {key}='{escaped}'")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export as JSON string."""
        import json
        return json.dumps(self._data, indent=2, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"EnvStore({self.path}, {len(self._data)} vars)"
