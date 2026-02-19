#!/usr/bin/env python3
"""getv Quick Start — centralized .env management in one folder.

Instead of scattered .env files in every project, keep all your
keys, credentials, and device configs in one place: ~/.getv/

    ~/.getv/
    ├── llm/
    │   ├── groq.env          → GROQ_API_KEY=gsk_xxx, LLM_MODEL=groq/llama-3.3-70b
    │   ├── openrouter.env    → OPENROUTER_API_KEY=sk-or-xxx, LLM_MODEL=openrouter/...
    │   └── ollama-local.env  → OLLAMA_API_BASE=http://localhost:11434, LLM_MODEL=ollama/llama3.2
    ├── devices/
    │   ├── rpi3.env          → RPI_HOST=192.168.1.10, RPI_USER=pi, RPI_PASSWORD=xxx
    │   └── nvidia.env        → SSH_HOST=192.168.1.50, SSH_USER=tom
    └── defaults/
        ├── fixpi.conf        → llm=groq, devices=rpi3
        └── prellm.conf       → llm=openrouter
"""

from getv import EnvStore, ProfileManager, AppDefaults

# --- Setup: create profiles programmatically ---

pm = ProfileManager("~/.getv")
pm.add_category("llm")
pm.add_category("devices")

# Create an LLM profile
pm.set("llm", "groq", {
    "LLM_MODEL": "groq/llama-3.3-70b-versatile",
    "GROQ_API_KEY": "gsk_your_key_here",
})

# Create a device profile
pm.set("devices", "rpi3", {
    "RPI_HOST": "192.168.1.10",
    "RPI_USER": "pi",
    "RPI_PASSWORD": "raspberry",
    "RPI_PORT": "22",
})

# --- Usage: read back ---

store = pm.get("llm", "groq")
print(f"Model: {store.get('LLM_MODEL')}")

# List all LLM profiles
for name, s in pm.list("llm"):
    print(f"  LLM profile: {name} → {s.get('LLM_MODEL')}")

# --- App defaults: each app picks its own profile ---

defaults = AppDefaults("my-app")
defaults.set("llm", "groq")
defaults.set("devices", "rpi3")

# Later, at startup:
llm_name = defaults.get("llm")      # "groq"
device_name = defaults.get("devices")  # "rpi3"
print(f"App defaults: llm={llm_name}, devices={device_name}")

# Merge profiles into one config dict
cfg = pm.merge_profiles({}, **defaults.as_profile_kwargs())
print(f"Merged config: {list(cfg.keys())}")
