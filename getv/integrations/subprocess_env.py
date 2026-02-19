"""getv integration for subprocess — run any command with profile env vars injected.

The core "pipe" mechanism: load a profile, inject its vars into a subprocess.

Usage::

    from getv.integrations.subprocess_env import SubprocessEnv

    # Run ssh with device profile vars
    result = SubprocessEnv.run("devices", "rpi3", ["ssh", "pi@192.168.1.10", "uname -a"])

    # Run ollama with llm profile
    result = SubprocessEnv.run("llm", "ollama-local", ["ollama", "run", "llama3.2"])

    # Run any command with merged profiles
    env = SubprocessEnv.build_env(devices="rpi3", llm="groq")
    result = SubprocessEnv.run_with_env(env, ["python", "my_script.py"])

    # Pipe-friendly: output env vars for shell eval
    print(SubprocessEnv.shell_export("llm", "groq"))
    # export GROQ_API_KEY='gsk_xxx'
    # export LLM_MODEL='groq/llama-3.3-70b-versatile'
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class SubprocessEnv:
    """Run subprocesses with getv profile env vars injected."""

    @staticmethod
    def build_env(base_dir: str | Path = "~/.getv", inherit: bool = True,
                  **profiles: Optional[str]) -> Dict[str, str]:
        """Build an env dict from multiple profiles.

        Args:
            base_dir: getv base directory.
            inherit: If True, start from os.environ and overlay profile vars.
            **profiles: category=profile_name pairs (e.g., devices="rpi3", llm="groq").
        """
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        env = dict(os.environ) if inherit else {}

        for category, name in profiles.items():
            if name is None:
                continue
            pm.add_category(category)
            store = pm.get(category, name)
            if store:
                env.update(store.as_dict())
        return env

    @staticmethod
    def run(category: str, profile_name: str, cmd: List[str],
            base_dir: str | Path = "~/.getv", capture: bool = False,
            timeout: Optional[int] = None, **kwargs) -> subprocess.CompletedProcess:
        """Run a command with a single profile's env vars injected."""
        env = SubprocessEnv.build_env(base_dir=base_dir, **{category: profile_name})
        return subprocess.run(cmd, env=env, capture_output=capture, text=True,
                              timeout=timeout, **kwargs)

    @staticmethod
    def run_with_env(env: Dict[str, str], cmd: List[str],
                     capture: bool = False, timeout: Optional[int] = None,
                     **kwargs) -> subprocess.CompletedProcess:
        """Run a command with a pre-built env dict."""
        return subprocess.run(cmd, env=env, capture_output=capture, text=True,
                              timeout=timeout, **kwargs)

    @staticmethod
    def shell_export(category: str, profile_name: str,
                     base_dir: str | Path = "~/.getv") -> str:
        """Generate shell export statements for eval.

        Usage in shell: eval $(getv export llm groq --format shell)
        """
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category(category)
        store = pm.get(category, profile_name)
        if store is None:
            return ""
        lines = []
        for k, v in sorted(store.as_dict().items()):
            # Escape single quotes in values
            escaped = v.replace("'", "'\\''")
            lines.append(f"export {k}='{escaped}'")
        return "\n".join(lines)

    @staticmethod
    def env_inline(category: str, profile_name: str,
                   base_dir: str | Path = "~/.getv") -> str:
        """Generate inline KEY=VALUE for prefixing commands.

        Usage: $(getv inline llm groq) ollama run llama3.2
        """
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category(category)
        store = pm.get(category, profile_name)
        if store is None:
            return ""
        parts = []
        for k, v in sorted(store.as_dict().items()):
            escaped = v.replace("'", "'\\''")
            parts.append(f"{k}='{escaped}'")
        return " ".join(parts)
