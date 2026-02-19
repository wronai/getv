#!/usr/bin/env python3
"""Use getv profiles with Pydantic Settings — inject before init.

Many projects (proxeen, etc.) use pydantic-settings BaseSettings.
getv can inject profile vars into os.environ before Settings() is created.

Setup:
    getv set llm groq GROQ_API_KEY=gsk_xxx LLM_MODEL=groq/llama3 VISION_MODEL=groq/llava
    getv use proxeen llm groq

In your app:
"""

from getv.integrations.pydantic_env import load_profile_into_env, profile_settings

# --- Option 1: Inject into env before Settings() ---

# This sets GROQ_API_KEY, LLM_MODEL etc. in os.environ
# so pydantic-settings picks them up automatically:

# load_profile_into_env("llm", "groq")
# settings = MySettings()  # reads from env

# --- Option 2: Use app defaults ---

# from getv import AppDefaults
# defaults = AppDefaults("proxeen")
# llm_name = defaults.get("llm", "ollama-local")
# load_profile_into_env("llm", llm_name)
# settings = MySettings()

# --- Option 3: Build Settings directly ---

# settings = profile_settings(MySettings, llm="groq", devices="rpi3")

print("Pydantic Settings integration ready.")
print("See source code for usage patterns.")
print()
print("Key concept: getv injects profile vars into os.environ,")
print("then pydantic-settings reads them as usual — zero changes to Settings class.")
