# getv — Universal .env Variable Manager

[![PyPI version](https://badge.fury.io/py/getv.svg)](https://badge.fury.io/py/getv)
[![Python versions](https://img.shields.io/pypi/pyversions/getv)](https://pypi.org/project/getv/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/pypi/dm/getv)](https://pypi.org/project/getv/)
[![Tests](https://github.com/wronai/getv/workflows/Tests/badge.svg)](https://github.com/wronai/getv/actions)

Read, write, encrypt, and delegate environment variables across services and devices.

![img.png](img.png)

Copy to the clipboard and run `getv grab` to detect and save the API key 

```bash
$ getv grab

Detected:  groq (GROQ_API_KEY)
Key:       gsk_Y1xV...TNpA
Source:    Prefix match
Domain:    console.groq.com
Category:  llm
Profile:   ~/.getv/llm/groq.env

Saved to /home/tom/.getv/llm/groq.env

Usage:
  getv get llm groq GROQ_API_KEY
  getv exec llm groq -- python app.py
```

without any plugins, managers, or integrations...


## 📑 Table of Contents

- [Why getv?](#why-getv)
- [Install](#install)
- [Quick Start](#quick-start)
- [Profile Directory Structure](#profile-directory-structure)
- [App Defaults](#app-defaults)
- [Integrations](#integrations)
- [Grab — Clipboard API Key Detection](#grab--clipboard-api-key-detection)
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

**v0.2.1** — New: `getv grab` (clipboard API key auto-detection), integrations, app defaults, 9 examples

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

## Grab — Clipboard API Key Detection

Copy an API key → run `getv grab` → auto-detected, saved.

```bash
# 1. Copy API key from console.groq.com (Ctrl+C)
# 2. Run:
getv grab

# Output:
# Detected:  groq (GROQ_API_KEY)
# Key:       gsk_abc1...9jkl
# Source:    Prefix match
# Domain:    console.groq.com
# Category:  llm
# Profile:   ~/.getv/llm/groq.env
# Saved to /home/user/.getv/llm/groq.env

# Options:
getv grab --dry-run           # detect only, don't save
getv grab --category api      # override category
getv grab --provider myname   # override provider name
getv grab --no-browser        # skip browser history check
```

### Supported prefixes (auto-detected)

| Prefix | Provider | Env Var | Category |
|--------|----------|---------|----------|
| `sk-ant-` | Anthropic | `ANTHROPIC_API_KEY` | llm |
| `sk-or-` | OpenRouter | `OPENROUTER_API_KEY` | llm |
| `sk-` / `sk-proj-` | OpenAI | `OPENAI_API_KEY` | llm |
| `gsk_` | Groq | `GROQ_API_KEY` | llm |
| `key-` | Mistral | `MISTRAL_API_KEY` | llm |
| `xai-` | xAI | `XAI_API_KEY` | llm |
| `pplx-` | Perplexity | `PERPLEXITY_API_KEY` | llm |
| `nvapi-` | NVIDIA | `NVIDIA_API_KEY` | llm |
| `hf_` | HuggingFace | `HF_API_KEY` | llm |
| `r8_` | Replicate | `REPLICATE_API_TOKEN` | llm |
| `ghp_` | GitHub | `GITHUB_TOKEN` | tokens |
| `glpat-` | GitLab | `GITLAB_TOKEN` | tokens |
| `AKIA` | AWS | `AWS_ACCESS_KEY_ID` | cloud |
| `dop_v1_` | DigitalOcean | `DIGITALOCEAN_TOKEN` | cloud |
| `tskey-` | Tailscale | `TAILSCALE_API_KEY` | tokens |
| `SG.` | SendGrid | `SENDGRID_API_KEY` | email |
| `sk_live_` / `sk_test_` | Stripe | `STRIPE_API_KEY` | payments |

### Detection priority

1. **Key prefix** — covers ~90% of cases (instant)
2. **Browser history** — Chrome/Firefox SQLite (last 10 min)
3. **User prompt** — fallback

```python
# Python API
from getv.integrations.clipboard import ClipboardGrab

grab = ClipboardGrab()
result = grab.detect()  # reads clipboard, returns GrabResult or None

if result:
    print(result.provider, result.env_var)
    result.save()  # writes to ~/.getv/llm/groq.env
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

### Real-world One-liners with Pipes & Hacks

#### 1. Source profile directly into shell

```bash
source <(getv exec llm groq -- env | grep -E '^(GROQ_API_KEY|LLM_MODEL)=')
```

**Problem:** Chcesz szybko załadować zmienne środowiskowe do bieżącej powłoki bez uruchamiania polecenia w `getv exec`.

**Rozwiązanie:** Process substitution `<(...)` pozwala traktować wyjście polecenia jako plik. Filtrujemy tylko interesujące nas zmienne.

**Wynik:** Zmienne `GROQ_API_KEY` i `LLM_MODEL` są dostępne w powłoce.

---

#### 2. Użycie z curl (wywołanie API)

```bash
getv exec llm groq -- curl -s https://api.groq.com/v1/models
```

**Problem:** Musisz wywołać API LLM z autentykacją, ale nie chcesz hardkodować klucza w skrypcie.

**Rozwiązanie:** `getv exec` automatycznie wstrzykuje zmienne środowiskowe z profilu przed uruchomieniem polecenia.

**Wynik:** Curl wysyła żądanie z nagłówkiem `Authorization: Bearer gsk_xxx`.

---

#### 3. Użycie z Pythonem

```bash
getv exec llm groq -- python -c "import os; print(os.environ['GROQ_API_KEY'][:10])"
```

**Problem:** Pythonowy skrypt potrzebuje klucza API, ale nie chcesz przekazywać go jako argument.
**Rozwiązanie:** Wstrzyknij profil do środowiska, Python czyta z `os.environ`.
**Wynik:** Skrypt widzi klucz bezpiecznie przechowywany w getv.

---

#### 4. Użycie z Docker (jako env file)

```bash
docker run --env-file <(getv export llm groq) python:3 python -c "import os; print('OK')"
```

**Problem:** Docker wymaga pliku `.env` ale nie chcesz tworzyć go ręcznie.
**Rozwiązanie:** Process substitution tworzy tymczasowy plik env na podstawie profilu getv.
**Wynik:** Kontener otrzymuje zmienne z profilu bez pliku na dysku.

---

#### 5. Export do .env

```bash
getv export llm groq > ~/.env.local && source ~/.env.local
```

**Problem:** Masz istniejący projekt który wymaga `.env` i chcesz użyć profilu getv.
**Rozwiązanie:** Export do standardowego formatu .env, następnie źródłujemy do powłoki.
**Wynik:** Wszystkie zmienne z profilu są dostępne w powłoce.

---

#### 6. Użycie z jq (przetwarzanie JSON)

```bash
getv exec llm groq -- curl -s https://api.groq.com/v1/models | jq '.data[0].id'
```

**Problem:** API zwraca JSON, chcesz wyciągnąć konkretne pole.
**Rozwiązanie:** Pipe JSON do jq do filtrowania.
**Wynik:** Wyświetla pierwszy dostępny model ID.

---

#### 7. Użycie z npx (np. Claude CLI)

```bash
getv exec llm groq -- npx -y @anthropic/claude-cli chat "hello"
```

**Problem:** Narzędzia npm potrzebują klucza API w środowisku.
**Rozwiązanie:** Wstrzyknij profil, npx uruchamia narzędzie z dostępnym kluczem.
**Wynik:** Claude CLI ma dostęp do API bez ręcznej konfiguracji.

---

#### 8. Użycie z litellm

```bash
getv exec llm groq -- litellm --model groq/llama-3.3-70b-versatile --temp 0 "hi"
```

**Problem:** LiteLLM to uniwersalny klient LLM, potrzebuje klucza i modelu.
**Rozwiązanie:** Profil dostarcza obie zmienne, litellm wykrywa providera po prefiksie klucza.
**Wynik:** Wywołanie LLM przez litellm z profilem groq.

---

#### 9. Użycie z ollama (lokalny model)

```bash
getv exec llm ollama -- ollama run llama3 "hello"
```

**Problem:** Ollama na zdalnym serwerze wymaga konfiguracji adresu i modelu.
**Rozwiązanie:** Profil zawiera `OLLAMA_API_BASE` i `OLLAMA_MODEL`, exec je wstrzykuje.
**Wynik:** Ollama łączy się ze zdalnym serwerem zamiast localhost.

---

#### 10. SSH do urządzenia z automatycznymi zmiennymi

```bash
getv ssh devices rpi3 "uptime"
```

**Problem:** SSH do urządzenia IoT, musisz pamiętać adres, użytkownika, port.
**Rozwiązanie:** Profil getv przechowuje wszystko, `getv ssh` automatycznie łączy.
**Wynik:** Zdalne polecenie wykonane bez ręcznego wpisywania parametrów.

---

#### 11. Rsync z użyciem profilu

```bash
getv exec devices rpi3 -- rsync -av /src/ rpi:/dest/
```

**Problem:** Rsync wymaga hosta, użytkownika - chcesz użyć profilu.
**Rozwiązanie:** Profil definiuje RPI_HOST i RPI_USER, rsync używa ich przez zmienne lub alias.
**Wynik:** Synchronizacja plików ze zdalnym urządzeniem.

---

#### 12. Import z istniejącego .env

```bash
getv import llm newprovider < .env
```

**Problem:** Masz istniejący plik .env i chcesz zaimportować do getv.
**Rozwiązanie:** `getv import` parsuje .env i zapisuje do profilu.
**Wynik:** Nowy profil `llm/newprovider` z wszystkimi zmiennymi.

---

#### 13. Watch - monitorowanie zmian

```bash
watch -n 5 'getv get llm groq GROQ_API_KEY'
```

**Problem:** Chcesz sprawdzić czy klucz się nie zmienił (np. po rotacji).
**Rozwiązanie:** Watch periodycznie odpytuje getv.
**Wynik:** Co 5 sekund wyświetla aktualną wartość klucza.

---

#### 14. Pipe do schowka (macOS)

```bash
getv get llm groq GROQ_API_KEY | pbcopy
```

**Problem:** Chcesz skopiować klucz do schowka ręcznie.
**Rozwiązanie:** Pipe wyjścia do `pbcopy` (macOS).
**Wynik:** Klucz w schowku gotowy do wklejenia.

---

#### 15. Łączenie profili (np. LLM + cloud razem)

```bash
cat <(getv export llm groq) <(getv export cloud aws) > combined.env
```

**Problem:** Potrzebujesz zmienne z wielu profili w jednym pliku.
**Rozwiązanie:** Process substitution łączy wyjście dwóch profilów.
**Wynik:** Plik combined.env ze zmiennymi z obu profili.

---

#### 16. Szybkie sprawdzenie wszystkich kluczy LLM

```bash
getv list llm --show-secrets | grep -E '^[A-Z_]+='
```

**Problem:** Chcesz zobaczyć wszystkie zmienne w kategori LLM.
**Rozwiązanie:** List z maskowaniem, filtruj grepem.
**Wynik:** Czysta lista KEY=VALUE bez格式化owania.

---

#### 17. Użycie z httpie (alternatywa dla curl)

```bash
getv exec llm openai -- https GET https://api.openai.com/v1/models
```

**Problem:** Wolisz httpie od curl dla lepszego formatowania.
**Rozwiązanie:** httpie automatycznie czyta zmienne środowiskowe.
**Wynik:** Ładnie sformatowane API response.

---

#### 18. Test połączenia z providerem

```bash
getv exec llm groq -- curl -s -w "\nHTTP: %{http_code}\n" https://api.groq.com/v1/models
```

**Problem:** Chcesz szybko sprawdzić czy klucz działa.
**Rozwiązanie:** curl z flagą `-w` pokazuje kod HTTP.
**Wynik:** Widzisz czy autentykacja przeszła (200) czy nie (401).

---

#### 19. Export dla crona

```bash
(crontab -l 2>/dev/null; echo "0 * * * * . <(getv export llm groq --format shell) && /usr/bin/python /app/sync.py") | crontab -
```

**Problem:** Cron potrzebuje zmiennych środowiskowych.
**Rozwiązanie:** Dodaj do crontab polecenie ładujące profil przed uruchomieniem.
**Wynik:** Cron job z dostępem do klucza API.

---

#### 20. Debug - pokaz wszystkie zmienne profilu

```bash
getv export llm groq --format shell | bash -x
```

**Problem:** Chcesz zobaczyć co dokładnie exportuje profil.
**Rozwiązanie:** Uruchom export jako skrypt z debug mode.
**Wynik:** Widzisz każde polecenie export i jego efekt.

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
| `getv grab [--dry-run]` | Auto-detect API key from clipboard and save |

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
| `09_grab_api_key.py` | Clipboard API key auto-detection |

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
pytest  # 128 tests
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
