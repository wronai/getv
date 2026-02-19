"""
getv — Universal .env variable manager.

Read, write, encrypt, and delegate environment variables across services and devices.
"""

from getv.store import EnvStore
from getv.profile import ProfileManager
from getv.security import mask_value, is_sensitive_key

__version__ = "0.1.1"

__all__ = [
    "EnvStore",
    "ProfileManager",
    "mask_value",
    "is_sensitive_key",
]
