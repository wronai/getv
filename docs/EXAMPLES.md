# One-liner Examples

Practical examples of getv in shell workflows — pipes, process substitution, and integrations.

## Popular API Tokens

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

# Multiple env vars at once
eval "$(getv export llm openai --format shell)" && python my_script.py

# Docker compose
getv export app production --format env > .env && docker-compose up
```

## Shell Integration

### Source profile into current shell

```bash
source <(getv exec llm groq -- env | grep -E '^(GROQ_API_KEY|LLM_MODEL)=')
```

Process substitution `<(...)` treats command output as a file. Filter only the vars you need.

### Export to .env for existing projects

```bash
getv export llm groq > ~/.env.local && source ~/.env.local
```

### Combine multiple profiles

```bash
cat <(getv export llm groq) <(getv export cloud aws) > combined.env
```

## API Calls

### curl with auth

```bash
getv exec llm groq -- curl -s https://api.groq.com/v1/models
```

`getv exec` injects env vars before running the command — no hardcoded keys.

### curl + jq

```bash
getv exec llm groq -- curl -s https://api.groq.com/v1/models | jq '.data[0].id'
```

### Test API connectivity

```bash
getv exec llm groq -- curl -s -w "\nHTTP: %{http_code}\n" https://api.groq.com/v1/models
```

### httpie (alternative to curl)

```bash
getv exec llm openai -- https GET https://api.openai.com/v1/models
```

## LLM Tools

### LiteLLM

```bash
getv exec llm groq -- litellm --model groq/llama-3.3-70b-versatile --temp 0 "hi"
```

### Ollama (remote server)

```bash
getv exec llm ollama -- ollama run llama3 "hello"
```

Profile provides `OLLAMA_API_BASE` and `OLLAMA_MODEL` — connects to remote instead of localhost.

### npx (e.g. Claude CLI)

```bash
getv exec llm groq -- npx -y @anthropic/claude-cli chat "hello"
```

## Device Management

### SSH

```bash
getv ssh rpi3 "uptime"
```

### Rsync with profile

```bash
getv exec devices rpi3 -- rsync -av /src/ rpi:/dest/
```

## Docker

### Process substitution env-file

```bash
docker run --env-file <(getv export llm groq) python:3 python -c "import os; print('OK')"
```

No temp file on disk — process substitution creates a virtual file.

## Python

```bash
getv exec llm groq -- python -c "import os; print(os.environ['GROQ_API_KEY'][:10])"
```

## Cron

```bash
(crontab -l 2>/dev/null; echo "0 * * * * . <(getv export llm groq --format shell) && python /app/sync.py") | crontab -
```

## Clipboard

```bash
# Copy key to clipboard (macOS)
getv get llm groq GROQ_API_KEY | pbcopy

# Linux (X11)
getv get llm groq GROQ_API_KEY | xclip -selection clipboard
```

## Debug

```bash
# Show what a profile exports
getv export llm groq --format shell | bash -x

# Watch for key rotation
watch -n 5 'getv get llm groq GROQ_API_KEY'

# List all LLM keys
getv list llm --show-secrets
```

## Python Examples

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
