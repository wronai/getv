"""getv integration for SSH — build ssh commands from device profiles.

Usage::

    from getv.integrations.ssh import SSHEnv

    ssh = SSHEnv.from_profile("rpi3")
    ssh.run("uname -a")                    # interactive
    print(ssh.command("ls /tmp"))           # ['sshpass', '-p', '***', 'ssh', '-p', '22', 'pi@192.168.1.10', 'ls /tmp']
    print(ssh.scp_to("local.txt", "/tmp")) # scp command
    print(ssh.connection_string())          # pi@192.168.1.10

    # Or just get the env dict for paramiko:
    params = ssh.as_paramiko_kwargs()
    # {"hostname": "192.168.1.10", "username": "pi", "password": "secret", "port": 22}
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SSHEnv:
    """SSH connection parameters from a getv device profile."""
    host: str = ""
    user: str = "pi"
    password: str = ""
    port: int = 22
    key_file: Optional[str] = None

    @classmethod
    def from_profile(cls, profile_name: str, base_dir: str | Path = "~/.getv") -> "SSHEnv":
        """Load SSH config from a getv device profile."""
        from getv.profile import ProfileManager
        pm = ProfileManager(base_dir)
        pm.add_category("devices")
        store = pm.get("devices", profile_name)
        if store is None:
            raise FileNotFoundError(f"Device profile not found: {profile_name}")
        return cls.from_dict(store.as_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "SSHEnv":
        return cls(
            host=data.get("RPI_HOST", data.get("SSH_HOST", data.get("HOST", ""))),
            user=data.get("RPI_USER", data.get("SSH_USER", data.get("USER", "pi"))),
            password=data.get("RPI_PASSWORD", data.get("SSH_PASSWORD", data.get("PASSWORD", ""))),
            port=int(data.get("RPI_PORT", data.get("SSH_PORT", data.get("PORT", "22")))),
            key_file=data.get("SSH_KEY_FILE", data.get("KEY_FILE", None)),
        )

    def connection_string(self) -> str:
        """user@host format."""
        return f"{self.user}@{self.host}"

    def command(self, remote_cmd: str = "") -> List[str]:
        """Build a full ssh command line as list of args.

        Uses sshpass if password is set and no key_file.
        """
        cmd: List[str] = []
        if self.password and not self.key_file:
            cmd.extend(["sshpass", "-p", self.password])
        cmd.append("ssh")
        if self.key_file:
            cmd.extend(["-i", self.key_file])
        cmd.extend(["-p", str(self.port)])
        cmd.extend(["-o", "StrictHostKeyChecking=no"])
        cmd.append(self.connection_string())
        if remote_cmd:
            cmd.append(remote_cmd)
        return cmd

    def scp_to(self, local_path: str, remote_path: str) -> List[str]:
        """Build scp command to upload a file."""
        cmd: List[str] = []
        if self.password and not self.key_file:
            cmd.extend(["sshpass", "-p", self.password])
        cmd.append("scp")
        if self.key_file:
            cmd.extend(["-i", self.key_file])
        cmd.extend(["-P", str(self.port)])
        cmd.extend(["-o", "StrictHostKeyChecking=no"])
        cmd.append(local_path)
        cmd.append(f"{self.connection_string()}:{remote_path}")
        return cmd

    def scp_from(self, remote_path: str, local_path: str) -> List[str]:
        """Build scp command to download a file."""
        cmd: List[str] = []
        if self.password and not self.key_file:
            cmd.extend(["sshpass", "-p", self.password])
        cmd.append("scp")
        if self.key_file:
            cmd.extend(["-i", self.key_file])
        cmd.extend(["-P", str(self.port)])
        cmd.extend(["-o", "StrictHostKeyChecking=no"])
        cmd.append(f"{self.connection_string()}:{remote_path}")
        cmd.append(local_path)
        return cmd

    def run(self, remote_cmd: str, capture: bool = False, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute a remote command via SSH."""
        cmd = self.command(remote_cmd)
        return subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )

    def as_paramiko_kwargs(self) -> Dict[str, Any]:
        """Return kwargs for paramiko.SSHClient.connect()."""
        kwargs: Dict[str, Any] = {
            "hostname": self.host,
            "username": self.user,
            "port": self.port,
        }
        if self.password:
            kwargs["password"] = self.password
        if self.key_file:
            kwargs["key_filename"] = self.key_file
        return kwargs

    def as_fabric_kwargs(self) -> Dict[str, Any]:
        """Return kwargs for fabric.Connection()."""
        kwargs: Dict[str, Any] = {
            "host": self.host,
            "user": self.user,
            "port": self.port,
        }
        connect_kwargs: Dict[str, str] = {}
        if self.password:
            connect_kwargs["password"] = self.password
        if self.key_file:
            kwargs["connect_kwargs"] = {"key_filename": self.key_file}
        if connect_kwargs:
            kwargs["connect_kwargs"] = connect_kwargs
        return kwargs
