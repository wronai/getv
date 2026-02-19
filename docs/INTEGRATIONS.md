# Integrations

getv ships with built-in integrations for common tools. No external plugins needed.

## SSH

```bash
# Setup once
getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PASSWORD=raspberry

# Connect
getv ssh rpi3                       # interactive shell
getv ssh rpi3 "uname -a"            # remote command
```

```python
from getv.integrations.ssh import SSHEnv
ssh = SSHEnv.from_profile("rpi3")
ssh.run("uname -a", capture=True)            # subprocess
params = ssh.as_paramiko_kwargs()            # for paramiko
```

## LiteLLM

```bash
# Setup providers
getv set llm groq LLM_MODEL=groq/llama-3.3-70b-versatile GROQ_API_KEY=gsk_xxx
getv set llm openrouter LLM_MODEL=openrouter/google/gemini-2.0-flash-exp:free OPENROUTER_API_KEY=sk-or-xxx

# Switch at runtime
getv exec llm groq -- python my_script.py
getv exec llm openrouter -- python my_script.py
```

```python
from getv.integrations.litellm import LiteLLMEnv
llm = LiteLLMEnv.from_profile("groq")
llm.activate()  # sets os.environ
# or: litellm.completion(**llm.as_completion_kwargs(), messages=[...])
```

## Ollama

```bash
getv set ollama gpu-server OLLAMA_API_BASE=http://192.168.1.50:11434 OLLAMA_MODEL=qwen2.5-coder:14b
getv exec ollama gpu-server -- ollama run qwen2.5-coder:14b
```

```python
from getv.integrations.ollama import OllamaEnv
oll = OllamaEnv.from_profile("gpu-server")
oll.activate()  # sets OLLAMA_API_BASE in env
print(oll.litellm_model())  # "ollama/qwen2.5-coder:14b"
```

## Docker

```bash
getv export llm groq --format docker > /tmp/groq.env
docker run --env-file /tmp/groq.env my-llm-app:latest
```

```python
from getv.integrations.docker import DockerEnv
denv = DockerEnv.from_profiles(llm="groq", devices="rpi3")
denv.write_env_file("/tmp/docker.env")
print(denv.compose_environment())  # docker-compose block
```

## curl

```bash
# API call with auth from profile
getv curl groq https://api.groq.com/openai/v1/models
getv curl openai https://api.openai.com/v1/models
```

## Pydantic Settings

```python
from getv.integrations.pydantic_env import load_profile_into_env
load_profile_into_env("llm", "groq")  # inject into os.environ
settings = MySettings()               # pydantic reads from env
```

## Subprocess / Pipe

```bash
# Run any command with profile env injected
getv exec llm groq -- python my_script.py
getv exec devices rpi3 -- ansible-playbook deploy.yml

# Shell eval
eval $(getv export llm groq --format shell)
```

## nfo (Log Redaction)

```python
from getv.integrations.nfo import patch_nfo_redaction
patch_nfo_redaction()  # nfo now uses getv's is_sensitive_key + mask_value
```

## File Watching

```python
from getv.watcher import EnvWatcher

def on_change(category, profile, store):
    print(f"Reloaded: {category}/{profile}")

with EnvWatcher("~/.getv", on_change=on_change):
    # profiles auto-reload while this block runs
    ...
```
