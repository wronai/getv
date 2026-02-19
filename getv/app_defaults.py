"""App-specific default profile selection.

Each application can register which profile it uses by default,
so different apps can use different LLM providers, devices, etc.

Storage::

    ~/.getv/defaults/
    ├── fixpi.conf       → devices=rpi3, llm=groq
    ├── prellm.conf      → llm=openrouter
    ├── marksync.conf     → llm=ollama
    └── curllm.conf       → llm=ollama

Usage::

    from getv.app_defaults import AppDefaults

    defaults = AppDefaults("fixpi")
    defaults.set("llm", "groq")
    defaults.set("devices", "rpi3")

    # Later, in fixpi startup:
    llm_name = defaults.get("llm")        # "groq"
    device_name = defaults.get("devices")  # "rpi3"

    # Or use with ProfileManager:
    pm = ProfileManager("~/.fixpi")
    cfg = pm.merge_profiles(base, **defaults.as_profile_kwargs())
    # equivalent to: pm.merge_profiles(base, devices="rpi3", llm="groq")
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


class AppDefaults:
    """Manage per-app default profile selections.

    Stored as simple key=value files in ~/.getv/defaults/APP.conf
    """

    def __init__(self, app_name: str, base_dir: str | Path = "~/.getv") -> None:
        self.app_name = app_name
        self.base_dir = Path(base_dir).expanduser().resolve()
        self._defaults_dir = self.base_dir / "defaults"
        self._defaults_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._defaults_dir / f"{app_name}.conf"
        self._data: Dict[str, str] = {}
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                self._data[k.strip()] = v.strip()

    def _save(self) -> None:
        lines = [f"# Default profiles for {self.app_name}"]
        for k, v in sorted(self._data.items()):
            lines.append(f"{k}={v}")
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def get(self, category: str, default: Optional[str] = None) -> Optional[str]:
        """Get default profile name for a category."""
        return self._data.get(category, default)

    def set(self, category: str, profile_name: str) -> "AppDefaults":
        """Set default profile for a category."""
        self._data[category] = profile_name
        self._save()
        return self

    def remove(self, category: str) -> "AppDefaults":
        """Remove a default."""
        self._data.pop(category, None)
        self._save()
        return self

    def as_dict(self) -> Dict[str, str]:
        """Return all defaults as {category: profile_name}."""
        return dict(self._data)

    def as_profile_kwargs(self) -> Dict[str, Optional[str]]:
        """Return defaults formatted for ProfileManager.merge_profiles(**kwargs)."""
        return dict(self._data)

    @staticmethod
    def list_apps(base_dir: str | Path = "~/.getv") -> List[str]:
        """List all apps that have defaults configured."""
        defaults_dir = Path(base_dir).expanduser().resolve() / "defaults"
        if not defaults_dir.exists():
            return []
        return sorted(f.stem for f in defaults_dir.glob("*.conf"))

    def __repr__(self) -> str:
        return f"AppDefaults({self.app_name!r}, {self._data})"
