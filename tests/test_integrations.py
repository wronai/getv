"""Tests for getv.integrations — litellm, ssh, ollama, docker, subprocess, curl."""

import os
import pytest
from pathlib import Path

from getv import ProfileManager


@pytest.fixture
def pm(tmp_path):
    """ProfileManager with test profiles."""
    pm = ProfileManager(str(tmp_path))
    pm.add_category("llm")
    pm.add_category("devices")
    pm.add_category("ollama")

    pm.set("llm", "groq", {
        "LLM_MODEL": "groq/llama-3.3-70b-versatile",
        "GROQ_API_KEY": "gsk_test_key_123",
    })
    pm.set("llm", "ollama-local", {
        "LLM_MODEL": "ollama/llama3.2",
        "OLLAMA_API_BASE": "http://localhost:11434",
    })
    pm.set("devices", "rpi3", {
        "RPI_HOST": "192.168.1.10",
        "RPI_USER": "pi",
        "RPI_PASSWORD": "raspberry",
        "RPI_PORT": "22",
    })
    pm.set("devices", "server", {
        "SSH_HOST": "10.0.0.5",
        "SSH_USER": "admin",
        "SSH_KEY_FILE": "~/.ssh/id_rsa",
    })
    pm.set("ollama", "local", {
        "OLLAMA_API_BASE": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.2",
        "OLLAMA_NUM_CTX": "8192",
    })
    return str(tmp_path)


class TestLiteLLMIntegration:
    def test_from_dict(self):
        from getv.integrations.litellm import LiteLLMEnv
        env = LiteLLMEnv.from_dict({
            "LLM_MODEL": "groq/llama-3.3-70b-versatile",
            "GROQ_API_KEY": "gsk_xxx",
        })
        assert env.model == "groq/llama-3.3-70b-versatile"
        assert env.provider == "groq"
        assert env.api_key == "gsk_xxx"

    def test_from_profile(self, pm):
        from getv.integrations.litellm import LiteLLMEnv
        env = LiteLLMEnv.from_profile("groq", base_dir=pm)
        assert env.model == "groq/llama-3.3-70b-versatile"
        assert env.api_key == "gsk_test_key_123"

    def test_as_completion_kwargs(self):
        from getv.integrations.litellm import LiteLLMEnv
        env = LiteLLMEnv(model="groq/llama3", api_key="key123", provider="groq")
        kwargs = env.as_completion_kwargs()
        assert kwargs["model"] == "groq/llama3"
        assert kwargs["api_key"] == "key123"

    def test_activate(self, pm, monkeypatch):
        from getv.integrations.litellm import LiteLLMEnv
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        env = LiteLLMEnv.from_profile("groq", base_dir=pm)
        env.activate()
        assert os.environ.get("GROQ_API_KEY") == "gsk_test_key_123"

    def test_detect_provider_ollama(self):
        from getv.integrations.litellm import LiteLLMEnv
        env = LiteLLMEnv.from_dict({"LLM_MODEL": "ollama/llama3.2"})
        assert env.provider == "ollama"

    def test_default_model(self):
        from getv.integrations.litellm import LiteLLMEnv
        assert "groq/" in LiteLLMEnv.default_model("groq")

    def test_provider_key_var(self):
        from getv.integrations.litellm import LiteLLMEnv
        assert LiteLLMEnv.provider_key_var("groq") == "GROQ_API_KEY"
        assert LiteLLMEnv.provider_key_var("ollama") == ""

    def test_profile_not_found(self, pm):
        from getv.integrations.litellm import LiteLLMEnv
        with pytest.raises(FileNotFoundError):
            LiteLLMEnv.from_profile("nonexistent", base_dir=pm)


class TestSSHIntegration:
    def test_from_dict_rpi(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv.from_dict({
            "RPI_HOST": "192.168.1.10",
            "RPI_USER": "pi",
            "RPI_PASSWORD": "secret",
            "RPI_PORT": "22",
        })
        assert ssh.host == "192.168.1.10"
        assert ssh.user == "pi"
        assert ssh.password == "secret"
        assert ssh.port == 22

    def test_from_dict_generic(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv.from_dict({
            "SSH_HOST": "10.0.0.5",
            "SSH_USER": "admin",
            "SSH_KEY_FILE": "~/.ssh/id_rsa",
        })
        assert ssh.host == "10.0.0.5"
        assert ssh.key_file == "~/.ssh/id_rsa"

    def test_from_profile(self, pm):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv.from_profile("rpi3", base_dir=pm)
        assert ssh.host == "192.168.1.10"
        assert ssh.user == "pi"

    def test_connection_string(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="tom")
        assert ssh.connection_string() == "tom@1.2.3.4"

    def test_command_with_password(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="pi", password="secret", port=22)
        cmd = ssh.command("uname -a")
        assert "sshpass" in cmd
        assert "-p" in cmd
        assert "secret" in cmd
        assert "pi@1.2.3.4" in cmd
        assert "uname -a" in cmd

    def test_command_with_key_file(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="tom", key_file="~/.ssh/id_rsa")
        cmd = ssh.command()
        assert "-i" in cmd
        assert "~/.ssh/id_rsa" in cmd
        assert "sshpass" not in cmd

    def test_scp_to(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="pi", password="pw")
        cmd = ssh.scp_to("local.txt", "/tmp/")
        assert "scp" in cmd
        assert "local.txt" in cmd
        assert "pi@1.2.3.4:/tmp/" in cmd

    def test_scp_from(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="pi", password="pw")
        cmd = ssh.scp_from("/tmp/remote.txt", "./local.txt")
        assert "pi@1.2.3.4:/tmp/remote.txt" in cmd
        assert "./local.txt" in cmd

    def test_paramiko_kwargs(self):
        from getv.integrations.ssh import SSHEnv
        ssh = SSHEnv(host="1.2.3.4", user="pi", password="pw", port=2222)
        k = ssh.as_paramiko_kwargs()
        assert k["hostname"] == "1.2.3.4"
        assert k["username"] == "pi"
        assert k["password"] == "pw"
        assert k["port"] == 2222

    def test_profile_not_found(self, pm):
        from getv.integrations.ssh import SSHEnv
        with pytest.raises(FileNotFoundError):
            SSHEnv.from_profile("nonexistent", base_dir=pm)


class TestOllamaIntegration:
    def test_from_dict(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv.from_dict({
            "OLLAMA_API_BASE": "http://gpu:11434",
            "OLLAMA_MODEL": "qwen2.5:14b",
            "OLLAMA_NUM_CTX": "16384",
        })
        assert oll.base_url == "http://gpu:11434"
        assert oll.model == "qwen2.5:14b"
        assert oll.num_ctx == 16384

    def test_from_dict_strips_prefix(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv.from_dict({"LLM_MODEL": "ollama/llama3.2"})
        assert oll.model == "llama3.2"

    def test_from_profile(self, pm):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv.from_profile("local", base_dir=pm)
        assert oll.base_url == "http://localhost:11434"
        assert oll.model == "llama3.2"

    def test_api_url(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(base_url="http://localhost:11434")
        assert oll.api_url("/api/generate") == "http://localhost:11434/api/generate"

    def test_run_command(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(model="llama3.2")
        cmd = oll.run_command("hello")
        assert cmd == ["ollama", "run", "llama3.2", "hello"]

    def test_pull_command(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(model="llama3.2")
        assert oll.pull_command() == ["ollama", "pull", "llama3.2"]

    def test_litellm_model(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(model="llama3.2")
        assert oll.litellm_model() == "ollama/llama3.2"

    def test_litellm_model_already_prefixed(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(model="ollama/llama3.2")
        assert oll.litellm_model() == "ollama/llama3.2"

    def test_as_litellm_kwargs(self):
        from getv.integrations.ollama import OllamaEnv
        oll = OllamaEnv(base_url="http://gpu:11434", model="qwen2.5:14b")
        k = oll.as_litellm_kwargs()
        assert k["model"] == "ollama/qwen2.5:14b"
        assert k["api_base"] == "http://gpu:11434"


class TestDockerIntegration:
    def test_from_profile(self, pm):
        from getv.integrations.docker import DockerEnv
        d = DockerEnv.from_profile("llm", "groq", base_dir=pm)
        data = d.as_dict()
        assert "LLM_MODEL" in data
        assert "GROQ_API_KEY" in data

    def test_write_env_file(self, pm, tmp_path):
        from getv.integrations.docker import DockerEnv
        d = DockerEnv({"KEY1": "val1", "KEY2": "val2"})
        p = d.write_env_file(tmp_path / "test.env")
        content = p.read_text()
        assert "KEY1=val1" in content
        assert "KEY2=val2" in content

    def test_run_command(self):
        from getv.integrations.docker import DockerEnv
        d = DockerEnv({"KEY": "val"})
        cmd = d.run_command("my-image", "python main.py")
        assert cmd[0] == "docker"
        assert "run" in cmd
        assert "-e" in cmd
        assert "KEY=val" in cmd
        assert "my-image" in cmd

    def test_compose_environment(self):
        from getv.integrations.docker import DockerEnv
        d = DockerEnv({"A": "1", "B": "2"})
        out = d.compose_environment()
        assert "environment:" in out
        assert "A=1" in out

    def test_from_profiles_merge(self, pm):
        from getv.integrations.docker import DockerEnv
        d = DockerEnv.from_profiles(base_dir=pm, llm="groq", devices="rpi3")
        data = d.as_dict()
        assert "GROQ_API_KEY" in data
        assert "RPI_HOST" in data


class TestSubprocessEnv:
    def test_build_env(self, pm):
        from getv.integrations.subprocess_env import SubprocessEnv
        env = SubprocessEnv.build_env(base_dir=pm, llm="groq")
        assert env.get("GROQ_API_KEY") == "gsk_test_key_123"
        assert "PATH" in env  # inherited from os.environ

    def test_build_env_no_inherit(self, pm):
        from getv.integrations.subprocess_env import SubprocessEnv
        env = SubprocessEnv.build_env(base_dir=pm, inherit=False, llm="groq")
        assert env.get("GROQ_API_KEY") == "gsk_test_key_123"
        assert "PATH" not in env

    def test_shell_export(self, pm):
        from getv.integrations.subprocess_env import SubprocessEnv
        out = SubprocessEnv.shell_export("llm", "groq", base_dir=pm)
        assert "export GROQ_API_KEY=" in out
        assert "export LLM_MODEL=" in out

    def test_env_inline(self, pm):
        from getv.integrations.subprocess_env import SubprocessEnv
        out = SubprocessEnv.env_inline("llm", "groq", base_dir=pm)
        assert "GROQ_API_KEY=" in out
        assert "LLM_MODEL=" in out


class TestCurlIntegration:
    def test_command_with_auth(self):
        from getv.integrations.curl import CurlEnv
        c = CurlEnv({"GROQ_API_KEY": "gsk_xxx", "LLM_MODEL": "groq/llama3"})
        cmd = c.command("https://api.groq.com/v1/models")
        assert "curl" in cmd
        assert any("Bearer gsk_xxx" in arg for arg in cmd)

    def test_command_no_auth(self):
        from getv.integrations.curl import CurlEnv
        c = CurlEnv({"SOME_VAR": "val"})
        cmd = c.command("https://example.com")
        assert not any("Authorization" in arg for arg in cmd)

    def test_chat_completion(self):
        from getv.integrations.curl import CurlEnv
        c = CurlEnv({"GROQ_API_KEY": "gsk_xxx", "LLM_MODEL": "groq/llama3"})
        cmd = c.chat_completion("hello", api_base="https://api.groq.com/openai/v1")
        assert "-d" in cmd
        assert any("chat/completions" in arg for arg in cmd)

    def test_from_profile(self, pm):
        from getv.integrations.curl import CurlEnv
        c = CurlEnv.from_profile("llm", "groq", base_dir=pm)
        cmd = c.command("https://api.groq.com/v1/models")
        assert any("Bearer" in arg for arg in cmd)
