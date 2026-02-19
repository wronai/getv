"""getv integration for Pydantic Settings — load profiles into BaseSettings.

Bridges getv profiles with pydantic-settings so you can override
Settings fields from a named profile without touching .env files.

Usage::

    from getv.integrations.pydantic_env import load_profile_into_env, profile_settings

    # Option 1: Inject profile vars into os.environ before Settings() init
    load_profile_into_env("llm", "groq")
    settings = MySettings()  # now picks up GROQ_API_KEY etc.

    # Option 2: Build a Settings instance directly from a profile
    settings = profile_settings(MySettings, llm="groq", devices="rpi3")

    # Option 3: Get a dict of overrides for Settings(**overrides)
    overrides = profile_overrides(MySettings, llm="groq")
    settings = MySettings(**overrides)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


def load_profile_into_env(category: str, profile_name: str,
                          base_dir: str | Path = "~/.getv",
                          override: bool = False) -> Dict[str, str]:
    """Load a getv profile's vars into os.environ.

    Args:
        category: Profile category (e.g., "llm", "devices").
        profile_name: Profile name (e.g., "groq", "rpi3").
        base_dir: getv base directory.
        override: If True, overwrite existing env vars. Default: only set if missing.

    Returns:
        Dict of vars that were actually set.
    """
    from getv.profile import ProfileManager
    pm = ProfileManager(base_dir)
    pm.add_category(category)
    store = pm.get(category, profile_name)
    if store is None:
        return {}
    applied: Dict[str, str] = {}
    for k, v in store.as_dict().items():
        if override or k not in os.environ:
            os.environ[k] = v
            applied[k] = v
    return applied


def profile_overrides(settings_cls: Type[T],
                      base_dir: str | Path = "~/.getv",
                      **profiles: Optional[str]) -> Dict[str, Any]:
    """Get profile vars mapped to Settings field names.

    Pydantic Settings fields are lowercase; env vars are UPPERCASE.
    This maps GROQ_API_KEY → groq_api_key if the field exists.

    Returns:
        Dict of field_name → value for Settings(**overrides).
    """
    from getv.profile import ProfileManager
    pm = ProfileManager(base_dir)
    data: Dict[str, str] = {}
    for category, name in profiles.items():
        if name is None:
            continue
        pm.add_category(category)
        store = pm.get(category, name)
        if store:
            data.update(store.as_dict())

    # Map env var names to pydantic field names
    try:
        field_names = set(settings_cls.model_fields.keys())
    except AttributeError:
        field_names = set(getattr(settings_cls, "__fields__", {}).keys())

    overrides: Dict[str, Any] = {}
    for env_key, value in data.items():
        field_name = env_key.lower()
        if field_name in field_names:
            overrides[field_name] = value
    return overrides


def profile_settings(settings_cls: Type[T],
                     base_dir: str | Path = "~/.getv",
                     **profiles: Optional[str]) -> T:
    """Create a Settings instance with profile vars injected into env.

    This is the simplest integration: inject → instantiate → done.
    """
    for category, name in profiles.items():
        if name:
            load_profile_into_env(category, name, base_dir=base_dir)
    return settings_cls()
