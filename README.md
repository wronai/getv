# getv — Universal .env Variable Manager

[![PyPI version](https://badge.fury.io/py/getv.svg)](https://badge.fury.io/py/getv)
[![Python versions](https://img.shields.io/pypi/pyversions/getv)](https://pypi.org/project/getv/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/pypi/dm/getv)](https://pypi.org/project/getv/)
[![Tests](https://github.com/wronai/getv/workflows/Tests/badge.svg)](https://github.com/wronai/getv/actions)

Read, write, encrypt, and delegate environment variables across services and devices.

## 📑 Table of Contents

- [Why getv?](#why-getv)
- [Install](#install)
- [Quick Start](#quick-start)
- [Profile Directory Structure](#profile-directory-structure)
- [App Defaults](#app-defaults)
- [Integrations](#integrations)
- [One-liner Examples](#one-liner-examples)
- [Security](#security)
- [Format Export](#format-export)
- [CLI Reference](#cli-reference)
- [Examples](#examples)
- [Environment Variables](#environment-variables)
- [Adopted by](#adopted-by)
- [License](#license)

## Why getv?

Every project reinvents `.env` parsing. `getv` provides one library for:

- **Reading/writing** `.env` files with comment preservation
- **Profile management** — named configs for devices, LLM providers, databases
- **App defaults** — per-app profile selection (`~/.getv/defaults/APP.conf`)
- **Integrations** — plugins for SSH, LiteLLM, Ollama, Docker, curl, Pydantic
- **Secret masking** — automatic detection and masking of passwords/keys in logs
- **Encryption** — Fernet-based encryption of sensitive values for safe transport
- **Format export** — dict, JSON, shell, docker-compose, pydantic BaseSettings
- **CLI** — manage profiles from the command line

## Install

```bash
pip install getv                   # core
pip install "getv[crypto]"         # + encryption (Fernet)
pip install "getv[pydantic]"       # + pydantic BaseSettings export
pip install "getv[all]"            # everything
```

**v0.2.0** — New integrations, app defaults, and 8 examples

## Quick Start

### Python API

```python
from getv import EnvStore, ProfileManager

# Single .env file
store = EnvStore("~/.myapp/.env")
store.set("DB_HOST", "localhost").set("DB_PORT", "5432").save()
print(store.get("DB_HOST"))  # "localhost"

# Profile manager — multiple named configs
pm = ProfileManager("~/.getv")
pm.add_category("devices", required_keys=["RPI_HOST", "RPI_USER"])
pm.add_category("llm", required_keys=["LLM_MODEL"])

pm.set("devices", "rpi3", {
    "RPI_HOST": "192.168.1.10",
    "RPI_USER": "pi",
    "RPI_PASSWORD": "secret",
    "RPI_PORT": "22",
})

pm.set("llm", "groq", {
    "LLM_MODEL": "groq/llama-3.3-70b-versatile",
    "GROQ_API_KEY": "gsk_xxx",
})

# Merge profiles on top of base config
base = {"APP_NAME": "myapp", "RPI_HOST": "default"}
cfg = pm.merge_profiles(base, devices="rpi3", llm="groq")
# cfg["RPI_HOST"] == "192.168.1.10" (overridden by device profile)
# cfg["LLM_MODEL"] == "groq/llama-3.3-70b-versatile"

# App-specific defaults
from getv.app_defaults import AppDefaults
defaults = AppDefaults("myapp")
defaults.set("llm", "groq").set("devices", "rpi3")
# Later: cfg = pm.merge_profiles(base, **defaults.as_profile_kwargs())
```

### CLI

```bash
# Set variables
getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PASSWORD=secret

# Get a single variable
getv get devices rpi3 RPI_HOST
# → 192.168.1.10

# List all categories
getv list
#   devices/ (2 profiles)
#   llm/ (3 profiles)

# List profiles in a category (secrets masked)
getv list devices
#   rpi3: RPI_HOST=192.168.1.10, RPI_USER=pi, RPI_PASSWORD=secr***

# Show all variables (unmasked)
getv list devices rpi3 --show-secrets

# Export to different formats
getv export devices rpi3 --format json
getv export devices rpi3 --format shell
getv export devices rpi3 --format pydantic
getv export llm groq --format docker

# Encrypt sensitive values (Fernet)
getv encrypt devices rpi3
# → Generated key: ~/.getv/.fernet.key
# → Encrypted sensitive values in devices/rpi3

# Decrypt
getv decrypt devices rpi3

# Delete a profile
getv delete devices old-rpi

# Execute commands with profile environment
getv exec llm groq -- python my_script.py
getv exec devices rpi3 -- ssh pi@host uname -a

# SSH to devices using profile
getv ssh rpi3                    # interactive shell
getv ssh rpi3 "uname -a"        # run remote command

# Make authenticated API calls
getv curl groq https://api.groq.com/openai/v1/models
getv curl openai https://api.openai.com/v1/models -X POST -d '{"model":"gpt-4"}'

# Set app-specific defaults
getv use myapp llm groq
getv use myapp devices rpi3

# Show app defaults
getv defaults              # list all apps
getv defaults myapp       # show myapp defaults
```

## Profile Directory Structure

```text
~/.getv/                       ← GETV_HOME (configurable)
├── .fernet.key                ← encryption key (chmod 600)
├── defaults/                  ← per-app default profile selections
│   ├── fixpi.conf             → llm=groq, devices=rpi3
│   ├── prellm.conf            → llm=openrouter
│   └── marksync.conf          → llm=ollama-local
├── devices/
│   ├── rpi3.env
│   ├── rpi4-prod.env
│   └── nvidia.env
├── llm/
│   ├── groq.env
│   ├── openrouter.env
│   └── ollama-local.env
└── ollama/
    ├── local.env
    └── gpu-server.env
```

Each `.env` file is a standard `KEY=VALUE` file:

```bash
# ~/.getv/devices/rpi3.env
RPI_HOST=192.168.1.10
RPI_USER=pi
RPI_PASSWORD=secret
RPI_PORT=22
```

## App Defaults

Each app remembers which profile to use — so `fixpi` uses Groq while `marksync` uses Ollama:

```bash
# Set defaults (one-time)
getv use fixpi llm groq
getv use fixpi devices rpi3
getv use prellm llm openrouter
getv use marksync llm ollama-local

# Check what's configured
getv defaults
#   fixpi: devices=rpi3, llm=groq
#   marksync: llm=ollama-local
#   prellm: llm=openrouter

# In your app startup code:
from getv import AppDefaults, ProfileManager
defaults = AppDefaults("fixpi")
pm = ProfileManager("~/.getv")
cfg = pm.merge_profiles({}, **defaults.as_profile_kwargs())
```

## Integrations

getv ships with plugins for common tools:

### SSH

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

### LiteLLM

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

### Ollama

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

### Docker

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

### curl

```bash
# API call with auth from profile
getv curl groq https://api.groq.com/openai/v1/models
getv curl openai https://api.openai.com/v1/models
```

### Pydantic Settings

```python
from getv.integrations.pydantic_env import load_profile_into_env
load_profile_into_env("llm", "groq")  # inject into os.environ
settings = MySettings()               # pydantic reads from env
```

### Subprocess / Pipe

```bash
# Run any command with profile env injected
getv exec llm groq -- python my_script.py
getv exec devices rpi3 -- ansible-playbook deploy.yml

# Shell eval
eval $(getv export llm groq --format shell)
```

## One-liner Examples

### Popular API Tokens

```bash
# OpenAI
export OPENAI_API_KEY=$(getv get llm openai OPENAI_API_KEY) && python my_script.py

# GitHub
git clone https://$(getv get git github GH_TOKEN)@github.com/user/repo.git

# AWS
export AWS_ACCESS_KEY_ID=$(getv get aws prod AWS_ACCESS_KEY_ID) && \
export AWS_SECRET_ACCESS_KEY=$(getv get aws prod AWS_SECRET_ACCESS_KEY) && \
aws s3 ls

# Docker Hub
echo $(getv get docker hub DOCKERHUB_TOKEN) | docker login --username user --password-stdin

# Slack
curl -X POST -H 'Authorization: Bearer '$(getv get chat slack SLACK_BOT_TOKEN) \
  -H 'Content-type: application/json' --data '{"text":"Hello"}' \
  https://slack.com/api/chat.postMessage

# Multiple env vars
eval "$(getv export llm openai --format shell)" && python my_script.py

# Docker compose
getv export app production --format env > .env && docker-compose up

# Direct API calls
getv curl openai https://api.openai.com/v1/models
getv curl groq https://api.groq.com/openai/v1/chat/completions -X POST -d '{"model":"llama3-70b"}'
```

## Security

### Automatic Secret Detection

Keys matching these patterns are automatically masked in display/logs:

`PASSWORD`, `PASSWD`, `SECRET`, `TOKEN`, `API_KEY`, `APIKEY`,
`PRIVATE_KEY`, `ACCESS_KEY`, `ACCESS_TOKEN`, `AUTH`, `CREDENTIAL`

```python
from getv.security import mask_dict, is_sensitive_key

data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret123"}
print(mask_dict(data))
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secr***"}
```

### Encryption for Transport

```python
from getv.security import generate_key, encrypt_store, decrypt_store

key = generate_key()
data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
encrypted = encrypt_store(data, key, only_sensitive=True)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "ENC:gAAA..."}

original = decrypt_store(encrypted, key)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
```

## Format Export

| Format | Function | Output |
|--------|----------|--------|
| dict | `store.as_dict()` | `{"KEY": "val"}` |
| JSON | `to_json(data)` | `{"KEY": "val"}` |
| Shell | `to_shell_export(data)` | `export KEY='val'` |
| Docker | `to_docker_env(data)` | `KEY=val` |
| .env | `to_env_file(data)` | `KEY=val` |
| Pydantic | `to_pydantic_settings(data)` | Python class source |
| Pydantic model | `to_pydantic_model(data)` | BaseSettings instance |

## CLI Reference

| Command | Description |
|---------|-------------|
| `getv set CATEGORY PROFILE KEY=VAL...` | Create/update a profile |
| `getv get CATEGORY PROFILE KEY` | Get a single value |
| `getv list [CATEGORY [PROFILE]]` | List categories, profiles, or vars |
| `getv delete CATEGORY PROFILE` | Delete a profile |
| `getv export CATEGORY PROFILE --format FMT` | Export (json/shell/docker/env/pydantic) |
| `getv encrypt CATEGORY PROFILE` | Encrypt sensitive values |
| `getv decrypt CATEGORY PROFILE` | Decrypt values |
| `getv exec CATEGORY PROFILE -- CMD...` | Run command with profile env |
| `getv use APP CATEGORY PROFILE` | Set app default profile |
| `getv defaults [APP]` | Show app defaults |
| `getv ssh PROFILE [CMD]` | SSH to device from profile |
| `getv curl PROFILE URL` | Authenticated API call |

## Examples

See `examples/` directory:

| File | Description |
|------|-------------|
| `01_quick_start.py` | Centralized .env management |
| `02_ssh_from_profile.py` | SSH/SCP with paramiko/fabric |
| `03_litellm_multi_provider.py` | Switch LLM providers |
| `04_ollama_config.py` | Ollama local/remote/Docker |
| `05_docker_env.py` | Docker env files & compose |
| `06_app_defaults.py` | Per-app default profiles |
| `07_pipe_and_shell.sh` | Shell integration & pipes |
| `08_pydantic_settings.py` | Pydantic Settings bridge |

## Environment Variables

| Variable | Default | Description |
|---------|---------|-------------|
| `GETV_HOME` | `~/.getv` | Base directory for profiles |

## Adopted by

Projects using getv for `.env` management:

- **[fixpi](https://github.com/zlecenia/c2004/tree/main/fixPI)** — SSH + LLM diagnostic agent
- **[prellm](https://github.com/wronai/prellm)** — LLM preprocessing proxy
- **[code2logic](https://github.com/wronai/code2logic)** — Code analysis engine
- **[amen](https://github.com/wronai/amen)** — Intent-iterative AI gateway
- **[marksync](https://github.com/wronai/marksync)** — Markdown sync server
- **[curllm](https://github.com/wronai/curllm)** — LLM-powered web automation

## Development

```bash
git clone https://github.com/wronai/getv.git
cd getv
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest  # 84 tests
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
