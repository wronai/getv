"""getv integration for Docker — generate env files, compose fragments, run with env.

Usage::

    from getv.integrations.docker import DockerEnv

    denv = DockerEnv.from_profile("llm", "groq")

    # Generate --env-file content
    denv.write_env_file("/tmp/docker.env")

    # Docker run with env vars
    print(denv.run_command("my-image:latest"))
    # ['docker', 'run', '--env-file', '/tmp/...', 'my-image:latest']

    # Docker compose environment block
    print(denv.compose_environment())
    # environment:
    #   - GROQ_API_KEY=gsk_xxx
    #   - LLM_MODEL=groq/llama3
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from getv.security import is_sensitive_key


class DockerEnv:
    """Docker environment injection from getv profiles."""

    def __init__(self, data: Dict[str, str]) -> None:
        self._data = dict(data)

    @classmethod
    def from_profile(cls, category: str, profile_name: str, base_dir: str | Path = "~/.getv") -> "DockerEnv":
        """Load env vars from a getv profile."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category(category)
        store = pm.get(category, profile_name)
        if store is None:
            raise FileNotFoundError(f"Profile not found: {category}/{profile_name}")
        return cls(store.as_dict())

    @classmethod
    def from_profiles(cls, base_dir: str | Path = "~/.getv", **profiles: Optional[str]) -> "DockerEnv":
        """Merge multiple profiles into one Docker env."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        data: Dict[str, str] = {}
        for category, name in profiles.items():
            if name is None:
                continue
            pm.add_category(category)
            store = pm.get(category, name)
            if store:
                data.update(store.as_dict())
        return cls(data)

    def write_env_file(self, path: str | Path) -> Path:
        """Write a Docker-compatible env file (KEY=VALUE, no quotes)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={v}" for k, v in sorted(self._data.items())]
        p.write_text("\n".join(lines) + "\n")
        return p

    def run_command(self, image: str, cmd: str = "", extra_args: Optional[List[str]] = None) -> List[str]:
        """Build docker run command with --env flags."""
        result = ["docker", "run"]
        for k, v in sorted(self._data.items()):
            result.extend(["-e", f"{k}={v}"])
        if extra_args:
            result.extend(extra_args)
        result.append(image)
        if cmd:
            result.extend(cmd.split())
        return result

    def run_command_env_file(self, image: str, cmd: str = "") -> List[str]:
        """Build docker run command with --env-file (writes temp file)."""
        tmp = Path(tempfile.mktemp(suffix=".env", prefix="getv_docker_"))
        self.write_env_file(tmp)
        result = ["docker", "run", "--env-file", str(tmp), image]
        if cmd:
            result.extend(cmd.split())
        return result

    def compose_environment(self) -> str:
        """Generate docker-compose environment: block."""
        lines = ["environment:"]
        for k, v in sorted(self._data.items()):
            lines.append(f"  - {k}={v}")
        return "\n".join(lines)

    def compose_env_file_entry(self, path: str = ".env") -> str:
        """Generate docker-compose env_file: block."""
        return f"env_file:\n  - {path}"

    def as_dict(self) -> Dict[str, str]:
        return dict(self._data)
