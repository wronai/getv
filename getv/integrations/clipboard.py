"""getv clipboard integration — auto-detect API keys from clipboard.

Reads the system clipboard, identifies the provider by key prefix,
and optionally checks browser history for context.

Usage::

    from getv.integrations.clipboard import ClipboardGrab

    grab = ClipboardGrab()
    result = grab.detect()

    if result:
        print(result.provider)    # "groq"
        print(result.env_var)     # "GROQ_API_KEY"
        print(result.key[:8])     # "gsk_abc1"
        print(result.source)      # "prefix"
        result.save()             # writes to ~/.getv/llm/groq.env

CLI::

    getv grab                     # grab from clipboard, auto-detect, save
    getv grab --dry-run           # detect only, don't save
    getv grab --category api      # save to api/ instead of llm/
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ─── Prefix → Provider mapping ───────────────────────────────────────────────

PREFIX_RULES: List[Tuple[str, str, str, str]] = [
    # (prefix,        provider,       env_var,                console_domain)
    ("sk-ant-",       "anthropic",    "ANTHROPIC_API_KEY",    "console.anthropic.com"),
    ("sk-or-",        "openrouter",   "OPENROUTER_API_KEY",   "openrouter.ai"),
    ("sk-proj-",      "openai",       "OPENAI_API_KEY",       "platform.openai.com"),
    ("sk-",           "openai",       "OPENAI_API_KEY",       "platform.openai.com"),
    ("gsk_",          "groq",         "GROQ_API_KEY",         "console.groq.com"),
    ("hf_",           "huggingface",  "HF_API_KEY",           "huggingface.co"),
    ("r8_",           "replicate",    "REPLICATE_API_TOKEN",  "replicate.com"),
    ("xai-",          "xai",          "XAI_API_KEY",          "console.x.ai"),
    ("key-",          "mistral",      "MISTRAL_API_KEY",      "console.mistral.ai"),
    ("pplx-",         "perplexity",   "PERPLEXITY_API_KEY",   "perplexity.ai"),
    ("nvapi-",        "nvidia",       "NVIDIA_API_KEY",       "build.nvidia.com"),
    ("ghp_",          "github",       "GITHUB_TOKEN",         "github.com"),
    ("glpat-",        "gitlab",       "GITLAB_TOKEN",         "gitlab.com"),
    ("SG.",           "sendgrid",     "SENDGRID_API_KEY",     "app.sendgrid.com"),
    ("sk_live_",      "stripe",       "STRIPE_API_KEY",       "dashboard.stripe.com"),
    ("sk_test_",      "stripe-test",  "STRIPE_API_KEY",       "dashboard.stripe.com"),
    ("AKIA",          "aws",          "AWS_ACCESS_KEY_ID",    "console.aws.amazon.com"),
    ("dop_v1_",       "digitalocean", "DIGITALOCEAN_TOKEN",   "cloud.digitalocean.com"),
    ("tskey-",        "tailscale",    "TAILSCALE_API_KEY",    "login.tailscale.com"),
]

# Domain → provider mapping for browser history fallback
DOMAIN_MAP: Dict[str, Tuple[str, str]] = {
    "console.anthropic.com":    ("anthropic",   "ANTHROPIC_API_KEY"),
    "platform.openai.com":      ("openai",      "OPENAI_API_KEY"),
    "console.groq.com":         ("groq",        "GROQ_API_KEY"),
    "openrouter.ai":            ("openrouter",  "OPENROUTER_API_KEY"),
    "console.mistral.ai":       ("mistral",     "MISTRAL_API_KEY"),
    "huggingface.co":           ("huggingface", "HF_API_KEY"),
    "replicate.com":            ("replicate",   "REPLICATE_API_TOKEN"),
    "console.x.ai":             ("xai",         "XAI_API_KEY"),
    "aistudio.google.com":      ("google",      "GOOGLE_API_KEY"),
    "build.nvidia.com":         ("nvidia",      "NVIDIA_API_KEY"),
    "dashboard.stripe.com":     ("stripe",      "STRIPE_API_KEY"),
    "app.sendgrid.com":         ("sendgrid",    "SENDGRID_API_KEY"),
    "dash.cloudflare.com":      ("cloudflare",  "CLOUDFLARE_API_KEY"),
    "console.cloud.google.com": ("gcp",         "GOOGLE_CLOUD_API_KEY"),
    "portal.azure.com":         ("azure",       "AZURE_API_KEY"),
    "console.aws.amazon.com":   ("aws",         "AWS_ACCESS_KEY_ID"),
    "cloud.digitalocean.com":   ("digitalocean","DIGITALOCEAN_TOKEN"),
    "vercel.com":               ("vercel",      "VERCEL_TOKEN"),
    "app.supabase.com":         ("supabase",    "SUPABASE_KEY"),
}

# Default category for each provider type
PROVIDER_CATEGORY: Dict[str, str] = {
    "anthropic": "llm", "openai": "llm", "groq": "llm", "openrouter": "llm",
    "mistral": "llm", "huggingface": "llm", "replicate": "llm", "xai": "llm",
    "perplexity": "llm", "nvidia": "llm", "google": "llm",
    "github": "tokens", "gitlab": "tokens", "tailscale": "tokens",
    "stripe": "payments", "stripe-test": "payments", "sendgrid": "email",
    "aws": "cloud", "gcp": "cloud", "azure": "cloud", "digitalocean": "cloud",
    "cloudflare": "cloud", "vercel": "cloud", "supabase": "cloud",
}


@dataclass
class GrabResult:
    """Result of clipboard grab + auto-detection."""
    key: str
    provider: str
    env_var: str
    source: str  # "prefix", "browser", "manual"
    domain: str = ""
    category: str = "llm"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def save(self, base_dir: str | Path = "~/.getv") -> Path:
        """Save to getv profile."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category(self.category)

        data = {self.env_var: self.key}
        if self.domain:
            data["_SOURCE_DOMAIN"] = self.domain
        data["_GRABBED_AT"] = self.timestamp

        pm.set(self.category, self.provider, data)
        base = Path(base_dir).expanduser().resolve()
        return base / self.category / f"{self.provider}.env"

    @property
    def masked_key(self) -> str:
        if len(self.key) > 12:
            return self.key[:8] + "..." + self.key[-4:]
        return self.key[:4] + "..."


class ClipboardGrab:
    """Auto-detect API keys from clipboard with multi-source detection."""

    def __init__(self, check_browser: bool = True, browser_minutes: int = 10) -> None:
        self.check_browser = check_browser
        self.browser_minutes = browser_minutes

    def read_clipboard(self) -> str:
        """Read text from system clipboard. Cross-platform."""
        # Try each clipboard tool in order
        for cmd in self._clipboard_commands():
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=2,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return ""

    @staticmethod
    def _clipboard_commands() -> List[List[str]]:
        """Platform-specific clipboard read commands."""
        if sys.platform == "darwin":
            return [["pbpaste"]]
        elif sys.platform == "win32":
            return [["powershell", "-command", "Get-Clipboard"]]
        else:
            # Linux: try X11, then Wayland
            return [
                ["xclip", "-selection", "clipboard", "-o"],
                ["xsel", "--clipboard", "--output"],
                ["wl-paste"],
            ]

    @staticmethod
    def detect_by_prefix(key: str) -> Optional[Tuple[str, str, str]]:
        """Detect provider by API key prefix.

        Returns (provider, env_var, domain) or None.
        """
        for prefix, provider, env_var, domain in PREFIX_RULES:
            if key.startswith(prefix):
                return provider, env_var, domain
        return None

    @staticmethod
    def looks_like_api_key(text: str) -> bool:
        """Heuristic: does this text look like an API key?"""
        if len(text) < 16 or len(text) > 256:
            return False
        if "\n" in text or "\t" in text:
            return False
        # Most API keys are alphanumeric + limited special chars
        if re.match(r'^[A-Za-z0-9_\-\.=+/]{16,256}$', text):
            return True
        return False

    def detect_from_browser_history(self) -> Optional[Tuple[str, str, str]]:
        """Check recent browser history for API console visits.

        Returns (provider, env_var, domain) or None.
        """
        if not self.check_browser:
            return None

        # Find Chrome/Chromium history
        chrome_paths = [
            Path.home() / ".config/google-chrome/Default/History",
            Path.home() / ".config/chromium/Default/History",
        ]
        if sys.platform == "darwin":
            chrome_paths.insert(0,
                Path.home() / "Library/Application Support/Google/Chrome/Default/History")

        for db_path in chrome_paths:
            result = self._search_sqlite_history(
                db_path,
                "SELECT url FROM urls WHERE url LIKE ? AND last_visit_time > ? ORDER BY last_visit_time DESC LIMIT 1",
                lambda minutes: int((time.time() + 11644473600) * 1_000_000) - minutes * 60 * 1_000_000,
            )
            if result:
                return result

        # Firefox history
        ff_dir = Path.home() / ".mozilla/firefox"
        if ff_dir.exists():
            for places in ff_dir.glob("*.default*/places.sqlite"):
                result = self._search_sqlite_history(
                    places,
                    "SELECT url FROM moz_places WHERE url LIKE ? AND last_visit_date > ? ORDER BY last_visit_date DESC LIMIT 1",
                    lambda minutes: int(time.time() * 1_000_000) - minutes * 60 * 1_000_000,
                )
                if result:
                    return result

        return None

    def _search_sqlite_history(self, db_path: Path, query: str,
                                time_func) -> Optional[Tuple[str, str, str]]:
        """Search a SQLite browser history database."""
        if not db_path.exists():
            return None

        # Copy the file (browser may lock it)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(tmp_fd)
        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            min_time = time_func(self.browser_minutes)

            for domain, (provider, env_var) in DOMAIN_MAP.items():
                try:
                    cursor.execute(query, (f"%{domain}%", min_time))
                    row = cursor.fetchone()
                    if row:
                        conn.close()
                        return provider, env_var, domain
                except sqlite3.Error:
                    continue
            conn.close()
        except (sqlite3.Error, OSError):
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return None

    def detect(self, text: Optional[str] = None) -> Optional[GrabResult]:
        """Full detection pipeline: clipboard → prefix → browser → None.

        Args:
            text: If provided, use this instead of reading clipboard.
        """
        key = text if text is not None else self.read_clipboard()
        if not key:
            return None

        key = key.strip()

        # Strategy 1: prefix matching (covers ~90% of cases)
        prefix_match = self.detect_by_prefix(key)
        if prefix_match:
            provider, env_var, domain = prefix_match
            category = PROVIDER_CATEGORY.get(provider, "llm")
            return GrabResult(
                key=key, provider=provider, env_var=env_var,
                source="prefix", domain=domain, category=category,
            )

        # Check if it even looks like an API key before more expensive checks
        if not self.looks_like_api_key(key):
            return None

        # Strategy 2: browser history
        browser_match = self.detect_from_browser_history()
        if browser_match:
            provider, env_var, domain = browser_match
            category = PROVIDER_CATEGORY.get(provider, "llm")
            return GrabResult(
                key=key, provider=provider, env_var=env_var,
                source="browser", domain=domain, category=category,
            )

        # Strategy 3: return as unknown (caller can prompt user)
        return GrabResult(
            key=key, provider="unknown", env_var="API_KEY",
            source="undetected", domain="", category="llm",
        )
