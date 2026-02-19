"""getv ↔ nfo integration — enhanced log redaction using getv.security patterns.

When both getv and nfo are installed, this module lets nfo use getv's
sensitive key detection and masking for log redaction. It also provides
a helper to load getv profiles into nfo's EnvTagger.

Usage::

    from getv.integrations.nfo import patch_nfo_redaction
    patch_nfo_redaction()  # nfo now uses getv's is_sensitive_key + mask_value

Or load profiles as env tags::

    from getv.integrations.nfo import profile_env_tagger
    tagger = profile_env_tagger("llm", "groq")
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def patch_nfo_redaction(visible_chars: int = 4) -> bool:
    """Monkey-patch nfo.redact to use getv.security for sensitive key detection.

    This gives nfo access to getv's pattern matching (which may be broader
    or more up-to-date than nfo's built-in patterns).

    Args:
        visible_chars: Number of leading chars to show in masked values.

    Returns:
        True if patched successfully, False if nfo not installed.
    """
    try:
        import nfo.redact as nfo_redact
    except ImportError:
        return False

    from getv.security import is_sensitive_key as getv_is_sensitive, mask_value

    # Save originals for combined detection
    _orig_is_sensitive = nfo_redact.is_sensitive_key

    def _combined_is_sensitive(key: str) -> bool:
        """Use both getv and nfo patterns for maximum coverage."""
        return getv_is_sensitive(key) or _orig_is_sensitive(key)

    def _getv_redact_value(value: str, visible_chars: int = visible_chars) -> str:
        """Use getv's mask_value style (show first N chars + ***)."""
        if not value:
            return "***REDACTED***"
        return mask_value(value, visible_chars)

    def _getv_redact_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in kwargs.items():
            if _combined_is_sensitive(key):
                if isinstance(value, str):
                    result[key] = _getv_redact_value(value)
                else:
                    result[key] = "***REDACTED***"
            else:
                result[key] = value
        return result

    # Patch nfo.redact module
    nfo_redact.is_sensitive_key = _combined_is_sensitive
    nfo_redact.redact_value = _getv_redact_value
    nfo_redact.redact_kwargs = _getv_redact_kwargs

    return True


def profile_env_tagger(category: str, profile: str,
                       base_dir: str = "~/.getv") -> Optional[Any]:
    """Create an nfo EnvTagger loaded with getv profile variables.

    Args:
        category: Profile category (e.g. "llm").
        profile: Profile name (e.g. "groq").
        base_dir: getv home directory.

    Returns:
        nfo.EnvTagger instance, or None if nfo not installed.
    """
    try:
        from nfo import EnvTagger
    except ImportError:
        return None

    from getv.profile import ProfileManager
    pm = ProfileManager(base_dir)
    data = pm.get_dict(category, profile)
    if not data:
        return None

    # EnvTagger reads from os.environ, so inject profile vars temporarily
    import os
    for k, v in data.items():
        if k not in os.environ:
            os.environ[k] = v

    return EnvTagger()


def redact_profile_display(category: str, profile: str,
                           base_dir: str = "~/.getv") -> Dict[str, str]:
    """Load a profile and return it with sensitive values redacted (for logging).

    Uses getv.security.mask_dict for consistent masking.
    """
    from getv.profile import ProfileManager
    from getv.security import mask_dict

    pm = ProfileManager(base_dir)
    data = pm.get_dict(category, profile)
    return mask_dict(data)
