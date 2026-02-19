"""Tests for getv.integrations.clipboard — API key auto-detection from clipboard."""

import pytest
from pathlib import Path

from getv.integrations.clipboard import (
    ClipboardGrab, GrabResult,
    PREFIX_RULES, DOMAIN_MAP, PROVIDER_CATEGORY,
)


class TestPrefixDetection:
    """Test detect_by_prefix for all known providers."""

    @pytest.mark.parametrize("key,expected_provider,expected_var", [
        ("sk-ant-abc123def456ghi789", "anthropic", "ANTHROPIC_API_KEY"),
        ("sk-or-v1-abc123def456ghi789", "openrouter", "OPENROUTER_API_KEY"),
        ("sk-proj-abc123def456ghi789", "openai", "OPENAI_API_KEY"),
        ("sk-abc123def456ghi789jkl", "openai", "OPENAI_API_KEY"),
        ("gsk_abc123def456ghi789jkl", "groq", "GROQ_API_KEY"),
        ("hf_abc123def456ghi789jkl", "huggingface", "HF_API_KEY"),
        ("r8_abc123def456ghi789jkl", "replicate", "REPLICATE_API_TOKEN"),
        ("xai-abc123def456ghi789jkl", "xai", "XAI_API_KEY"),
        ("key-abc123def456ghi789jkl", "mistral", "MISTRAL_API_KEY"),
        ("pplx-abc123def456ghi789jkl", "perplexity", "PERPLEXITY_API_KEY"),
        ("nvapi-abc123def456ghi789jkl", "nvidia", "NVIDIA_API_KEY"),
        ("ghp_abc123def456ghi789jkl", "github", "GITHUB_TOKEN"),
        ("glpat-abc123def456ghi789jkl", "gitlab", "GITLAB_TOKEN"),
        ("SG.abc123def456ghi789jkl", "sendgrid", "SENDGRID_API_KEY"),
        ("sk_" + "live_abc123def456ghi789", "stripe", "STRIPE_API_KEY"),
        ("sk_" + "test_abc123def456ghi789", "stripe-test", "STRIPE_API_KEY"),
        ("AKIAIOSFODNN7EXAMPLE12", "aws", "AWS_ACCESS_KEY_ID"),
        ("dop_v1_abc123def456ghi789", "digitalocean", "DIGITALOCEAN_TOKEN"),
        ("tskey-abc123def456ghi789jkl", "tailscale", "TAILSCALE_API_KEY"),
    ])
    def test_known_prefixes(self, key, expected_provider, expected_var):
        result = ClipboardGrab.detect_by_prefix(key)
        assert result is not None, f"Failed to detect prefix for {key[:10]}..."
        provider, env_var, domain = result
        assert provider == expected_provider
        assert env_var == expected_var

    def test_unknown_prefix(self):
        assert ClipboardGrab.detect_by_prefix("unknown_key_12345") is None

    def test_empty_string(self):
        assert ClipboardGrab.detect_by_prefix("") is None

    def test_prefix_order_sk_ant_before_sk(self):
        """sk-ant- must match anthropic, not openai."""
        result = ClipboardGrab.detect_by_prefix("sk-ant-api03-XXXXXXXXX")
        assert result[0] == "anthropic"

    def test_prefix_order_sk_or_before_sk(self):
        """sk-or- must match openrouter, not openai."""
        result = ClipboardGrab.detect_by_prefix("sk-or-v1-XXXXXXXXX")
        assert result[0] == "openrouter"


class TestLooksLikeApiKey:

    def test_valid_keys(self):
        assert ClipboardGrab.looks_like_api_key("gsk_abc123def456ghi789jkl") is True
        assert ClipboardGrab.looks_like_api_key("sk-proj-" + "a" * 40) is True
        assert ClipboardGrab.looks_like_api_key("A" * 32) is True

    def test_too_short(self):
        assert ClipboardGrab.looks_like_api_key("abc") is False
        assert ClipboardGrab.looks_like_api_key("short") is False

    def test_too_long(self):
        assert ClipboardGrab.looks_like_api_key("a" * 300) is False

    def test_multiline(self):
        assert ClipboardGrab.looks_like_api_key("line1\nline2") is False

    def test_with_tabs(self):
        assert ClipboardGrab.looks_like_api_key("key\twith\ttabs") is False

    def test_with_spaces(self):
        assert ClipboardGrab.looks_like_api_key("key with spaces here") is False

    def test_empty(self):
        assert ClipboardGrab.looks_like_api_key("") is False


class TestGrabResult:

    def test_masked_key_long(self):
        r = GrabResult(key="gsk_abc123def456ghi789jkl", provider="groq",
                       env_var="GROQ_API_KEY", source="prefix")
        masked = r.masked_key
        assert masked.startswith("gsk_abc1")
        assert masked.endswith("9jkl")
        assert "..." in masked

    def test_masked_key_short(self):
        r = GrabResult(key="short_key_1234", provider="x", env_var="X", source="prefix")
        masked = r.masked_key
        assert masked.startswith("shor")
        assert "..." in masked

    def test_save(self, tmp_path):
        r = GrabResult(
            key="gsk_test_key_123456789012",
            provider="groq",
            env_var="GROQ_API_KEY",
            source="prefix",
            domain="console.groq.com",
            category="llm",
        )
        path = r.save(base_dir=str(tmp_path))
        assert path.exists()
        content = path.read_text()
        assert "GROQ_API_KEY=gsk_test_key_123456789012" in content
        assert "_SOURCE_DOMAIN=console.groq.com" in content
        assert "_GRABBED_AT=" in content

    def test_save_creates_category_dir(self, tmp_path):
        r = GrabResult(key="test_key_1234567890", provider="custom",
                       env_var="CUSTOM_KEY", source="manual", category="tokens")
        path = r.save(base_dir=str(tmp_path))
        assert (tmp_path / "tokens").is_dir()
        assert path.exists()


class TestFullDetectPipeline:

    def test_detect_groq(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("gsk_abc123def456ghi789jkl012345")
        assert result is not None
        assert result.provider == "groq"
        assert result.env_var == "GROQ_API_KEY"
        assert result.source == "prefix"
        assert result.category == "llm"

    def test_detect_anthropic(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXX")
        assert result.provider == "anthropic"
        assert result.env_var == "ANTHROPIC_API_KEY"

    def test_detect_github(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        assert result.provider == "github"
        assert result.env_var == "GITHUB_TOKEN"
        assert result.category == "tokens"

    def test_detect_stripe(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("sk_" + "live_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        assert result.provider == "stripe"
        assert result.category == "payments"

    def test_detect_aws(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("AKIAIOSFODNN7EXAMPLE12")
        assert result.provider == "aws"
        assert result.category == "cloud"

    def test_detect_unknown_key(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("some_unknown_but_long_enough_key_string_here")
        assert result is not None
        assert result.source == "undetected"
        assert result.provider == "unknown"

    def test_detect_empty(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("")
        assert result is None

    def test_detect_not_a_key(self):
        grab = ClipboardGrab(check_browser=False)
        result = grab.detect("hello world")
        assert result is None


class TestProviderCategoryMapping:
    """Ensure all prefix providers have a category assigned."""

    def test_all_prefix_providers_have_category(self):
        for _, provider, _, _ in PREFIX_RULES:
            assert provider in PROVIDER_CATEGORY, \
                f"Provider {provider} from PREFIX_RULES missing in PROVIDER_CATEGORY"

    def test_all_domain_providers_have_category(self):
        for domain, (provider, _) in DOMAIN_MAP.items():
            assert provider in PROVIDER_CATEGORY, \
                f"Provider {provider} ({domain}) from DOMAIN_MAP missing in PROVIDER_CATEGORY"
