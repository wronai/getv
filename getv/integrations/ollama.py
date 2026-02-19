"""getv integration for Ollama — configure and launch Ollama from profiles.

Usage::

    from getv.integrations.ollama import OllamaEnv

    oll = OllamaEnv.from_profile("ollama-local")
    print(oll.base_url)       # http://localhost:11434
    print(oll.model)          # llama3.2

    # Set env for litellm/ollama
    oll.activate()

    # Build ollama CLI commands
    print(oll.run_command("Why is the sky blue?"))
    # ['ollama', 'run', 'llama3.2', 'Why is the sky blue?']

    # API URL for REST calls
    print(oll.api_url("/api/generate"))
    # http://localhost:11434/api/generate
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class OllamaEnv:
    """Ollama configuration from a getv profile."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    num_ctx: int = 4096
    temperature: float = 0.7
    host: str = ""

    @classmethod
    def from_profile(cls, profile_name: str, base_dir: str | Path = "~/.getv") -> "OllamaEnv":
        """Load Ollama config from a getv profile."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category("ollama")
        store = pm.get("ollama", profile_name)
        if store is None:
            # Try llm category
            pm.add_category("llm")
            store = pm.get("llm", profile_name)
        if store is None:
            raise FileNotFoundError(f"Ollama profile not found: {profile_name}")
        return cls.from_dict(store.as_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "OllamaEnv":
        model = data.get("OLLAMA_MODEL", data.get("LLM_MODEL", "llama3.2"))
        if model.startswith("ollama/"):
            model = model[len("ollama/"):]
        return cls(
            base_url=data.get("OLLAMA_API_BASE", data.get("OLLAMA_URL", "http://localhost:11434")),
            model=model,
            num_ctx=int(data.get("OLLAMA_NUM_CTX", data.get("NUM_CTX", "4096"))),
            temperature=float(data.get("OLLAMA_TEMPERATURE", data.get("TEMPERATURE", "0.7"))),
            host=data.get("OLLAMA_HOST", ""),
        )

    def activate(self) -> None:
        """Set os.environ for Ollama/litellm usage."""
        os.environ["OLLAMA_API_BASE"] = self.base_url
        if self.host:
            os.environ["OLLAMA_HOST"] = self.host

    def api_url(self, path: str = "") -> str:
        """Build full API URL."""
        base = self.base_url.rstrip("/")
        return f"{base}{path}" if path else base

    def run_command(self, prompt: str = "") -> List[str]:
        """Build ollama CLI command."""
        cmd = ["ollama", "run", self.model]
        if prompt:
            cmd.append(prompt)
        return cmd

    def pull_command(self) -> List[str]:
        """Build ollama pull command."""
        return ["ollama", "pull", self.model]

    def litellm_model(self) -> str:
        """Return model string with ollama/ prefix for litellm."""
        if self.model.startswith("ollama/"):
            return self.model
        return f"ollama/{self.model}"

    def as_litellm_kwargs(self) -> Dict[str, str]:
        """Return kwargs for litellm.completion()."""
        return {
            "model": self.litellm_model(),
            "api_base": self.base_url,
        }
