"""getv integration for curl — build authenticated API calls from profiles.

Usage::

    from getv.integrations.curl import CurlEnv

    curl = CurlEnv.from_profile("llm", "groq")
    print(curl.command("https://api.groq.com/openai/v1/models"))
    # ['curl', '-H', 'Authorization: Bearer gsk_xxx', 'https://api.groq.com/...']

    # For OpenAI-compatible APIs
    cmd = curl.chat_completion("What is 2+2?", model="groq/llama-3.3-70b-versatile")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from getv.integrations.litellm import PROVIDER_KEY_MAP


class CurlEnv:
    """Build curl commands with auth headers from getv profiles."""

    def __init__(self, data: Dict[str, str]) -> None:
        self._data = dict(data)
        self._api_key = ""
        self._api_base = ""
        self._detect_auth()

    def _detect_auth(self) -> None:
        for name, info in PROVIDER_KEY_MAP.items():
            key_var = info.get("key_var", "")
            if key_var and self._data.get(key_var):
                self._api_key = self._data[key_var]
                base_var = info.get("base_var", "")
                if base_var and self._data.get(base_var):
                    self._api_base = self._data[base_var]
                break
        # Fallback to generic keys
        if not self._api_key:
            for k in ("API_KEY", "AUTH_TOKEN", "TOKEN", "BEARER_TOKEN"):
                if self._data.get(k):
                    self._api_key = self._data[k]
                    break

    @classmethod
    def from_profile(cls, category: str, profile_name: str,
                     base_dir: str | Path = "~/.getv") -> "CurlEnv":
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category(category)
        store = pm.get(category, profile_name)
        if store is None:
            raise FileNotFoundError(f"Profile not found: {category}/{profile_name}")
        return cls(store.as_dict())

    def command(self, url: str, method: str = "GET",
                data: Optional[str] = None,
                headers: Optional[Dict[str, str]] = None) -> List[str]:
        """Build a curl command with auth."""
        cmd = ["curl", "-s"]
        if method != "GET":
            cmd.extend(["-X", method])
        if self._api_key:
            cmd.extend(["-H", f"Authorization: Bearer {self._api_key}"])
        cmd.extend(["-H", "Content-Type: application/json"])
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        if data:
            cmd.extend(["-d", data])
        cmd.append(url)
        return cmd

    def chat_completion(self, message: str, model: Optional[str] = None,
                        api_base: Optional[str] = None) -> List[str]:
        """Build a curl command for OpenAI-compatible chat completion."""
        base = api_base or self._api_base or "https://api.openai.com/v1"
        base = base.rstrip("/")
        url = f"{base}/chat/completions"
        mdl = model or self._data.get("LLM_MODEL", "gpt-4o-mini")
        payload = json.dumps({
            "model": mdl,
            "messages": [{"role": "user", "content": message}],
        })
        return self.command(url, method="POST", data=payload)
