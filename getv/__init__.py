"""
getv — Universal .env variable manager.

Read, write, encrypt, and delegate environment variables across services and devices.
"""

from getv.store import EnvStore
from getv.profile import ProfileManager, ProfileValidationError
from getv.security import mask_value, is_sensitive_key
from getv.app_defaults import AppDefaults
from getv.watcher import EnvWatcher

__version__ = "0.2.10"

__all__ = [
    "EnvStore",
    "ProfileManager",
    "ProfileValidationError",
    "AppDefaults",
    "EnvWatcher",
    "mask_value",
    "is_sensitive_key",
]
