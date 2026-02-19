"""
getv — Universal .env variable manager.

Read, write, encrypt, and delegate environment variables across services and devices.
"""

from getv.store import EnvStore
from getv.profile import ProfileManager
from getv.security import mask_value, is_sensitive_key
from getv.app_defaults import AppDefaults

__version__ = "0.1.4"

__all__ = [
    "EnvStore",
    "ProfileManager",
    "AppDefaults",
    "mask_value",
    "is_sensitive_key",
]
