"""Security utilities — masking, encryption, sensitive key detection."""

from __future__ import annotations

import re
from typing import Dict, Optional, Set

# Keys whose values should be masked in logs/display
_SENSITIVE_PATTERNS: Set[str] = {
    "PASSWORD", "PASSWD", "PASS",
    "SECRET", "TOKEN",
    "API_KEY", "APIKEY",
    "PRIVATE_KEY", "PRIVATE",
    "ACCESS_KEY", "ACCESS_TOKEN",
    "AUTH", "AUTHORIZATION",
    "CREDENTIAL", "CREDENTIALS",
}

_SENSITIVE_RE = re.compile(
    r"(" + "|".join(re.escape(p) for p in _SENSITIVE_PATTERNS) + r")",
    re.IGNORECASE,
)


def is_sensitive_key(key: str) -> bool:
    """Check if a key name likely holds a secret value."""
    return bool(_SENSITIVE_RE.search(key))


def mask_value(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive value, showing only first N chars."""
    if len(value) <= visible_chars:
        return "***"
    return value[:visible_chars] + "***"


def mask_dict(data: Dict[str, str], visible_chars: int = 4) -> Dict[str, str]:
    """Return a copy with sensitive values masked."""
    result = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            result[key] = mask_value(value, visible_chars)
        else:
            result[key] = value
    return result


# ── Encryption (optional, requires cryptography) ────────────────────────

def encrypt_value(value: str, key: bytes) -> str:
    """Encrypt a string value using Fernet symmetric encryption.

    Args:
        value: Plaintext string to encrypt.
        key: 32-byte URL-safe base64-encoded Fernet key.

    Returns:
        Encrypted token as a string.
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise ImportError("Install getv[crypto] for encryption: pip install getv[crypto]")
    f = Fernet(key)
    return f.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_value(token: str, key: bytes) -> str:
    """Decrypt a Fernet-encrypted token back to plaintext."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise ImportError("Install getv[crypto] for encryption: pip install getv[crypto]")
    f = Fernet(key)
    return f.decrypt(token.encode("ascii")).decode("utf-8")


def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise ImportError("Install getv[crypto] for encryption: pip install getv[crypto]")
    return Fernet.generate_key()


def encrypt_store(data: Dict[str, str], key: bytes, only_sensitive: bool = True) -> Dict[str, str]:
    """Encrypt values in a dict for safe transport.

    Args:
        data: Key-value pairs to encrypt.
        key: Fernet key.
        only_sensitive: If True, only encrypt values whose keys match sensitive patterns.

    Returns:
        Dict with encrypted values prefixed with 'ENC:'.
    """
    result = {}
    for k, v in data.items():
        if only_sensitive and not is_sensitive_key(k):
            result[k] = v
        else:
            result[k] = f"ENC:{encrypt_value(v, key)}"
    return result


def decrypt_store(data: Dict[str, str], key: bytes) -> Dict[str, str]:
    """Decrypt values that were encrypted by encrypt_store."""
    result = {}
    for k, v in data.items():
        if v.startswith("ENC:"):
            result[k] = decrypt_value(v[4:], key)
        else:
            result[k] = v
    return result
