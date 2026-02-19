"""getv integration for LiteLLM — provider key maps, model resolution, env setup.

Eliminates the need for every project to maintain its own PROVIDER_KEY_MAP.

Usage::

    from getv.integrations.litellm import LiteLLMEnv

    # Load LLM profile and inject into os.environ for litellm
    llm = LiteLLMEnv.from_profile("groq")
    llm.activate()  # sets os.environ keys

    # Or get completion kwargs directly
    import litellm
    resp = litellm.completion(model=llm.model, messages=[...])

    # Check which providers are configured
    configured = LiteLLMEnv.check_providers()
    # {"groq": True, "openai": False, "ollama": True, ...}
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from getv.store import EnvStore

# Canonical provider → env key mapping (shared across all wronai projects)
PROVIDER_KEY_MAP: Dict[str, Dict[str, str]] = {
    "openai":       {"key_var": "OPENAI_API_KEY",      "base_var": "OPENAI_BASE_URL",     "prefix": ""},
    "anthropic":    {"key_var": "ANTHROPIC_API_KEY",    "base_var": "ANTHROPIC_BASE_URL",  "prefix": "anthropic/"},
    "groq":         {"key_var": "GROQ_API_KEY",         "base_var": "GROQ_BASE_URL",       "prefix": "groq/"},
    "mistral":      {"key_var": "MISTRAL_API_KEY",      "base_var": "MISTRAL_BASE_URL",    "prefix": "mistral/"},
    "openrouter":   {"key_var": "OPENROUTER_API_KEY",   "base_var": "OPENROUTER_API_BASE", "prefix": "openrouter/"},
    "deepseek":     {"key_var": "DEEPSEEK_API_KEY",     "base_var": "DEEPSEEK_API_BASE",   "prefix": "deepseek/"},
    "gemini":       {"key_var": "GEMINI_API_KEY",       "base_var": "GEMINI_API_BASE",     "prefix": "gemini/"},
    "together_ai":  {"key_var": "TOGETHERAI_API_KEY",   "base_var": "TOGETHERAI_API_BASE", "prefix": "together_ai/"},
    "ollama":       {"key_var": "",                     "base_var": "OLLAMA_API_BASE",     "prefix": "ollama/"},
    "azure":        {"key_var": "AZURE_API_KEY",        "base_var": "AZURE_API_BASE",      "prefix": "azure/"},
}

# Default models per provider
DEFAULT_MODELS: Dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "anthropic/claude-3-5-sonnet-20241022",
    "groq": "groq/llama-3.3-70b-versatile",
    "mistral": "mistral/mistral-large-latest",
    "openrouter": "openrouter/google/gemini-2.0-flash-exp:free",
    "deepseek": "deepseek/deepseek-chat",
    "gemini": "gemini/gemini-2.0-flash",
    "together_ai": "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "ollama": "ollama/llama3.2",
    "azure": "azure/gpt-4o",
}


@dataclass
class LiteLLMEnv:
    """Resolved LiteLLM environment from a getv profile."""
    model: str = ""
    api_key: str = ""
    api_base: str = ""
    provider: str = ""
    extra_env: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_profile(cls, profile_name: str, base_dir: str | Path = "~/.getv") -> "LiteLLMEnv":
        """Load LLM config from a getv profile.

        Looks in: ~/.getv/llm/NAME.env
        """
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category("llm")
        store = pm.get("llm", profile_name)
        if store is None:
            raise FileNotFoundError(f"LLM profile not found: {profile_name}")
        data = store.as_dict()
        return cls.from_dict(data)

    @classmethod
    def from_env_file(cls, path: str | Path) -> "LiteLLMEnv":
        """Load from a specific .env file."""
        store = EnvStore(path, auto_create=False)
        return cls.from_dict(store.as_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "LiteLLMEnv":
        """Resolve LiteLLM config from a dict of env vars."""
        model = data.get("LLM_MODEL", "")
        provider = cls._detect_provider(model, data)
        info = PROVIDER_KEY_MAP.get(provider, {})

        api_key = ""
        if info.get("key_var"):
            api_key = data.get(info["key_var"], "")

        api_base = ""
        if info.get("base_var"):
            api_base = data.get(info["base_var"], "")

        return cls(
            model=model,
            api_key=api_key,
            api_base=api_base,
            provider=provider,
            extra_env={k: v for k, v in data.items()
                       if k not in ("LLM_MODEL", info.get("key_var", ""), info.get("base_var", ""))},
        )

    @staticmethod
    def _detect_provider(model: str, data: Dict[str, str]) -> str:
        """Detect provider from model string or env keys."""
        for name, info in PROVIDER_KEY_MAP.items():
            prefix = info.get("prefix", "")
            if prefix and model.startswith(prefix):
                return name
        # Fallback: check which API keys are present
        for name, info in PROVIDER_KEY_MAP.items():
            if info.get("key_var") and data.get(info["key_var"]):
                return name
        return "openai"

    def activate(self) -> None:
        """Inject this config into os.environ for litellm."""
        info = PROVIDER_KEY_MAP.get(self.provider, {})
        if self.api_key and info.get("key_var"):
            os.environ[info["key_var"]] = self.api_key
        if self.api_base and info.get("base_var"):
            os.environ[info["base_var"]] = self.api_base
        for k, v in self.extra_env.items():
            os.environ[k] = v

    def as_completion_kwargs(self) -> Dict[str, Any]:
        """Return kwargs for litellm.completion(model=..., api_key=..., api_base=...)."""
        kwargs: Dict[str, Any] = {"model": self.model}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        return kwargs

    @staticmethod
    def check_providers(base_dir: str | Path = "~/.getv") -> Dict[str, bool]:
        """Check which LLM providers have profiles configured."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category("llm")
        result: Dict[str, bool] = {}
        for name, store in pm.list("llm"):
            result[name] = bool(store.get("LLM_MODEL"))
        return result

    @staticmethod
    def default_model(provider: str) -> str:
        """Get default model for a provider."""
        return DEFAULT_MODELS.get(provider, "")

    @staticmethod
    def provider_key_var(provider: str) -> str:
        """Get the env var name for a provider's API key."""
        return PROVIDER_KEY_MAP.get(provider, {}).get("key_var", "")
