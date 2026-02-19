#!/usr/bin/env bash
# getv shell integration — pipe env vars to any command
#
# These examples show how getv replaces scattered .env files
# with a single source of truth for all your tools.

# ============================================================
# 1. EXPORT: inject profile vars into current shell
# ============================================================

# Load Groq LLM vars into current shell session
eval $(getv export llm groq --format shell)
# Now: $GROQ_API_KEY, $LLM_MODEL are set in this shell

# Verify
echo "LLM_MODEL=$LLM_MODEL"


# ============================================================
# 2. EXEC: run a command with profile vars injected
# ============================================================

# Run a Python script with Groq env vars
getv exec llm groq -- python my_llm_app.py

# Run ollama with specific profile
getv exec ollama gpu-server -- ollama run qwen2.5-coder:14b

# SSH to a device using its profile
getv exec devices rpi3 -- ssh $RPI_USER@$RPI_HOST

# Or use the shortcut:
getv ssh rpi3 "uname -a"


# ============================================================
# 3. CURL: API calls with auto-injected auth
# ============================================================

# List Groq models (auth header injected automatically)
getv curl groq https://api.groq.com/openai/v1/models

# Query OpenAI
getv curl openai https://api.openai.com/v1/models

# Works with any profile that has API keys


# ============================================================
# 4. DOCKER: generate env files for containers
# ============================================================

# Write a Docker env file from a profile
getv export llm groq --format docker > /tmp/groq.env
docker run --env-file /tmp/groq.env my-llm-app:latest

# Or inline
docker run $(getv export llm groq --format shell | sed 's/export /-e /g') my-app


# ============================================================
# 5. APP DEFAULTS: each app remembers its profile
# ============================================================

# Set defaults
getv use fixpi llm groq
getv use fixpi devices rpi3
getv use prellm llm openrouter
getv use marksync llm ollama-local

# Check defaults
getv defaults
getv defaults fixpi

# Switch a default
getv use fixpi llm openrouter

# List all profiles
getv list llm
getv list devices


# ============================================================
# 6. COMMON WORKFLOWS
# ============================================================

# Setup a new LLM provider
getv set llm groq \
    LLM_MODEL=groq/llama-3.3-70b-versatile \
    GROQ_API_KEY=gsk_your_key_here

# Setup a new device
getv set devices rpi4 \
    RPI_HOST=192.168.1.20 \
    RPI_USER=pi \
    RPI_PASSWORD=raspberry \
    RPI_PORT=22

# Setup an Ollama instance
getv set ollama gpu-server \
    OLLAMA_API_BASE=http://192.168.1.50:11434 \
    OLLAMA_MODEL=qwen2.5-coder:14b

# Encrypt sensitive values
getv encrypt llm groq
getv encrypt devices rpi4

# Export for backup
getv export llm groq --format json > backup-groq.json
