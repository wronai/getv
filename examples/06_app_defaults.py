#!/usr/bin/env python3
"""Per-app default profiles — each app picks its own LLM, device, etc.

The key idea: you have multiple LLM profiles (groq, openrouter, ollama)
and multiple apps (fixpi, prellm, marksync). Each app remembers which
profile to use by default.

Setup:
    getv use fixpi llm groq
    getv use fixpi devices rpi3
    getv use prellm llm openrouter
    getv use marksync llm ollama-local
    getv use curllm ollama local

Check defaults:
    getv defaults              # all apps
    getv defaults fixpi        # just fixpi

In your app's startup code:
"""

from getv import AppDefaults, ProfileManager

# --- App-specific setup (done once by the user or CLI) ---

defaults = AppDefaults("my-cool-app")
defaults.set("llm", "groq")
defaults.set("devices", "rpi3")

# --- App startup: load the user's chosen profiles ---

app_defaults = AppDefaults("my-cool-app")
llm_profile = app_defaults.get("llm")         # "groq"
device_profile = app_defaults.get("devices")   # "rpi3"

print(f"App will use: llm={llm_profile}, devices={device_profile}")

# Merge into a flat config dict
pm = ProfileManager("~/.getv")
pm.add_category("llm")
pm.add_category("devices")
cfg = pm.merge_profiles({}, **app_defaults.as_profile_kwargs())
print(f"Resolved config keys: {sorted(cfg.keys())}")

# --- List all apps that have defaults ---

all_apps = AppDefaults.list_apps()
print(f"\nApps with defaults: {all_apps}")
for app_name in all_apps:
    d = AppDefaults(app_name)
    print(f"  {app_name}: {d.as_dict()}")

# --- Override at runtime ---
# The user can always override via CLI:
#   getv exec llm openrouter -- python my-cool-app.py
# This runs the app with openrouter's env vars regardless of defaults.
