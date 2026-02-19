#!/usr/bin/env python3
"""Manage Ollama instances with getv — local, remote, Docker.

Setup profiles:
    getv set ollama local OLLAMA_API_BASE=http://localhost:11434 OLLAMA_MODEL=llama3.2
    getv set ollama gpu-server OLLAMA_API_BASE=http://192.168.1.50:11434 OLLAMA_MODEL=qwen2.5-coder:14b
    getv set ollama docker OLLAMA_API_BASE=http://host.docker.internal:11434 OLLAMA_MODEL=llama3.2

Switch:
    getv exec ollama gpu-server -- ollama run qwen2.5-coder:14b
    getv use curllm ollama gpu-server
"""

from getv.integrations.ollama import OllamaEnv

# --- Load Ollama config from profile ---

try:
    oll = OllamaEnv.from_profile("local")
    print(f"Ollama config:")
    print(f"  Base URL: {oll.base_url}")
    print(f"  Model:    {oll.model}")
    print(f"  Num CTX:  {oll.num_ctx}")

    # CLI commands
    print(f"\n  Run:  {' '.join(oll.run_command('Why is the sky blue?'))}")
    print(f"  Pull: {' '.join(oll.pull_command())}")

    # API URL for REST calls
    print(f"\n  API generate: {oll.api_url('/api/generate')}")
    print(f"  API tags:     {oll.api_url('/api/tags')}")

    # For litellm
    print(f"\n  LiteLLM model: {oll.litellm_model()}")
    print(f"  LiteLLM kwargs: {oll.as_litellm_kwargs()}")

    # Activate in current process
    # oll.activate()

except FileNotFoundError:
    print("No 'local' Ollama profile. Create one:")
    print("  getv set ollama local OLLAMA_API_BASE=http://localhost:11434 OLLAMA_MODEL=llama3.2")
