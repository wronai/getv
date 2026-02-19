"""ProfileManager — manage named .env profiles in directory trees."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from getv.store import EnvStore
from getv.security import mask_dict


class ProfileValidationError(ValueError):
    """Raised when a profile fails required_keys validation."""

    def __init__(self, category: str, name: str, missing: List[str]) -> None:
        self.category = category
        self.name = name
        self.missing = missing
        super().__init__(
            f"Profile {category}/{name} missing required keys: {', '.join(missing)}"
        )


class ProfileManager:
    """
    Manages collections of .env profiles organized in directories.

    Default layout::

        ~/.fixpi/
        ├── devices/
        │   ├── rpi3.env
        │   └── rpi4-prod.env
        └── llm/
            ├── groq.env
            └── openrouter.env

    Usage::

        pm = ProfileManager("~/.fixpi")
        pm.add_category("devices", required_keys=["RPI_HOST", "RPI_USER"])
        pm.add_category("llm", required_keys=["LLM_MODEL"])

        # Create a profile
        pm.set("devices", "rpi3", {"RPI_HOST": "192.168.1.10", "RPI_USER": "pi"})

        # Load a profile
        cfg = pm.get("devices", "rpi3")

        # List all profiles in a category
        for name, store in pm.list("devices"):
            print(name, store.get("RPI_HOST"))

        # Merge device + llm profiles on top of a base config
        merged = pm.merge_profiles(base_cfg, device="rpi3", llm="groq")
    """

    def __init__(self, base_dir: str | Path = "~/.getv") -> None:
        self.base_dir = Path(base_dir).expanduser().resolve()
        self._categories: Dict[str, dict] = {}

    def add_category(
        self,
        name: str,
        required_keys: Optional[List[str]] = None,
        defaults: Optional[Dict[str, str]] = None,
    ) -> "ProfileManager":
        """Register a profile category (e.g. 'devices', 'llm')."""
        self._categories[name] = {
            "required_keys": required_keys or [],
            "defaults": defaults or {},
        }
        cat_dir = self.base_dir / name
        cat_dir.mkdir(parents=True, exist_ok=True)
        return self

    def _category_dir(self, category: str) -> Path:
        d = self.base_dir / category
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _profile_path(self, category: str, name: str) -> Path:
        return self._category_dir(category) / f"{name}.env"

    # ── CRUD ─────────────────────────────────────────────────────────────

    def get(self, category: str, name: str) -> Optional[EnvStore]:
        """Load a profile by category and name. Returns None if not found."""
        path = self._profile_path(category, name)
        if not path.exists():
            return None
        return EnvStore(path, auto_create=False)

    def get_dict(self, category: str, name: str) -> Dict[str, str]:
        """Load profile as a plain dict. Returns {} if not found."""
        store = self.get(category, name)
        return store.as_dict() if store else {}

    def set(self, category: str, name: str, data: Dict[str, str],
            validate: bool = False) -> EnvStore:
        """Create or update a profile.

        Args:
            validate: If True, enforce required_keys for this category.
                      Raises ProfileValidationError on missing keys.
        """
        if validate:
            missing = self.validate(category, data)
            if missing:
                raise ProfileValidationError(category, name, missing)
        path = self._profile_path(category, name)
        store = EnvStore(path)
        store.update(data)
        store.save()
        return store

    def validate(self, category: str, data: Dict[str, str]) -> List[str]:
        """Check data against required_keys for category. Returns list of missing keys."""
        cat_info = self._categories.get(category, {})
        required = cat_info.get("required_keys", [])
        return [k for k in required if k not in data or not data[k]]

    def delete(self, category: str, name: str) -> bool:
        """Delete a profile. Returns True if it existed."""
        path = self._profile_path(category, name)
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, category: str, name: str) -> bool:
        return self._profile_path(category, name).exists()

    # ── List / Search ────────────────────────────────────────────────────

    def list(self, category: str) -> List[Tuple[str, EnvStore]]:
        """List all profiles in a category as (name, EnvStore) pairs."""
        cat_dir = self._category_dir(category)
        results = []
        for f in sorted(cat_dir.glob("*.env")):
            results.append((f.stem, EnvStore(f, auto_create=False)))
        return results

    def list_names(self, category: str) -> List[str]:
        """List profile names in a category."""
        return [name for name, _ in self.list(category)]

    def list_categories(self) -> List[str]:
        """List all registered categories."""
        return list(self._categories.keys())

    def list_all(self) -> Dict[str, List[Tuple[str, Dict[str, str]]]]:
        """Return all categories with their profiles as dicts."""
        result = {}
        for cat in self._categories:
            result[cat] = [
                (name, store.as_dict()) for name, store in self.list(cat)
            ]
        return result

    # ── Merge / Overlay ──────────────────────────────────────────────────

    def merge_profiles(
        self,
        base: Dict[str, str],
        **profiles: Optional[str],
    ) -> Dict[str, str]:
        """
        Merge named profiles on top of a base config.

        Example::

            merged = pm.merge_profiles(
                base_cfg,
                devices="rpi3",
                llm="groq",
            )
        """
        result = dict(base)
        for category, name in profiles.items():
            if name is None:
                continue
            store = self.get(category, name)
            if store:
                result.update(store.as_dict())
        return result

    # ── Search across profiles ───────────────────────────────────────────

    def find_by_key(self, category: str, key: str, value: str) -> List[str]:
        """Find profile names where key matches value."""
        matches = []
        for name, store in self.list(category):
            if store.get(key) == value:
                matches.append(name)
        return matches

    # ── Diff / Copy ────────────────────────────────────────────────────

    def diff(self, category: str, name_a: str, name_b: str) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """Compare two profiles. Returns {key: (value_a, value_b)} for differing keys.

        Keys present only in A have value_b=None, and vice versa.
        """
        a = self.get_dict(category, name_a)
        b = self.get_dict(category, name_b)
        all_keys = sorted(set(a) | set(b))
        result: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        for k in all_keys:
            va, vb = a.get(k), b.get(k)
            if va != vb:
                result[k] = (va, vb)
        return result

    def copy(self, src_category: str, src_name: str,
             dst_category: str, dst_name: str) -> EnvStore:
        """Clone a profile. Destination is overwritten if it exists."""
        data = self.get_dict(src_category, src_name)
        if not data:
            raise FileNotFoundError(f"Source profile not found: {src_category}/{src_name}")
        self.add_category(dst_category)
        return self.set(dst_category, dst_name, data)

    # ── Display helpers ──────────────────────────────────────────────────

    def list_table(self, category: str, columns: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """Return profiles as list of dicts with masked sensitive values, suitable for table display."""
        rows = []
        for name, store in self.list(category):
            data = mask_dict(store.as_dict())
            row = {"name": name, **data}
            if columns:
                row = {k: row.get(k, "") for k in ["name"] + columns}
            rows.append(row)
        return rows

    def __repr__(self) -> str:
        cats = ", ".join(self._categories.keys()) if self._categories else "none"
        return f"ProfileManager({self.base_dir}, categories=[{cats}])"
