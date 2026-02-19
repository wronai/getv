"""
getv — Universal .env variable manager.

Read, write, encrypt, and delegate environment variables across services and devices.
"""

from getv.store import EnvStore
from getv.profile import ProfileManager, ProfileValidationError
from getv.security import mask_value, is_sensitive_key
from getv.app_defaults import AppDefaults

__version__ = "0.2.7"

__all__ = [
    "EnvStore",
    "ProfileManager",
    "ProfileValidationError",
    "AppDefaults",
    "mask_value",
    "is_sensitive_key",
]
