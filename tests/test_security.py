"""Tests for getv.security."""

import pytest
from getv.security import (
    is_sensitive_key, mask_value, mask_dict,
    encrypt_value, decrypt_value, generate_key,
    encrypt_store, decrypt_store,
)


def test_is_sensitive_key():
    assert is_sensitive_key("RPI_PASSWORD") is True
    assert is_sensitive_key("DB_PASSWORD") is True
    assert is_sensitive_key("API_KEY") is True
    assert is_sensitive_key("OPENROUTER_API_KEY") is True
    assert is_sensitive_key("SECRET_TOKEN") is True
    assert is_sensitive_key("ACCESS_TOKEN") is True
    assert is_sensitive_key("AUTH_HEADER") is True
    assert is_sensitive_key("PRIVATE_KEY") is True
    # Not sensitive
    assert is_sensitive_key("RPI_HOST") is False
    assert is_sensitive_key("DB_PORT") is False
    assert is_sensitive_key("LLM_MODEL") is False
    assert is_sensitive_key("APP_NAME") is False


def test_mask_value():
    assert mask_value("supersecretpassword") == "supe***"
    assert mask_value("supersecretpassword", visible_chars=8) == "supersec***"
    assert mask_value("ab") == "***"
    assert mask_value("") == "***"


def test_mask_dict():
    data = {
        "RPI_HOST": "192.168.1.10",
        "RPI_PASSWORD": "mysecret",
        "API_KEY": "sk-1234567890",
        "LLM_MODEL": "groq/llama3",
    }
    masked = mask_dict(data)
    assert masked["RPI_HOST"] == "192.168.1.10"  # not sensitive
    assert masked["LLM_MODEL"] == "groq/llama3"  # not sensitive
    assert masked["RPI_PASSWORD"] == "myse***"
    assert masked["API_KEY"] == "sk-1***"


def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    original = "my_secret_value_123"
    encrypted = encrypt_value(original, key)
    assert encrypted != original
    decrypted = decrypt_value(encrypted, key)
    assert decrypted == original


def test_encrypt_store_only_sensitive():
    key = generate_key()
    data = {
        "RPI_HOST": "192.168.1.10",
        "RPI_PASSWORD": "secret",
        "LLM_MODEL": "groq/llama3",
        "API_KEY": "sk-123",
    }
    encrypted = encrypt_store(data, key, only_sensitive=True)
    assert encrypted["RPI_HOST"] == "192.168.1.10"  # not encrypted
    assert encrypted["LLM_MODEL"] == "groq/llama3"  # not encrypted
    assert encrypted["RPI_PASSWORD"].startswith("ENC:")
    assert encrypted["API_KEY"].startswith("ENC:")


def test_encrypt_decrypt_store_roundtrip():
    key = generate_key()
    data = {
        "RPI_HOST": "192.168.1.10",
        "RPI_PASSWORD": "secret",
        "API_KEY": "sk-123",
    }
    encrypted = encrypt_store(data, key, only_sensitive=True)
    decrypted = decrypt_store(encrypted, key)
    assert decrypted == data
