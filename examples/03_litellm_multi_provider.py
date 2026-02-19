#!/usr/bin/env python3
"""Switch LLM providers instantly with getv — no code changes needed.

Setup profiles once:
    getv set llm groq LLM_MODEL=groq/llama-3.3-70b-versatile GROQ_API_KEY=gsk_xxx
    getv set llm openrouter LLM_MODEL=openrouter/google/gemini-2.0-flash-exp:free OPENROUTER_API_KEY=sk-or-xxx
    getv set llm ollama-local LLM_MODEL=ollama/llama3.2 OLLAMA_API_BASE=http://localhost:11434
    getv set llm deepseek LLM_MODEL=deepseek/deepseek-chat DEEPSEEK_API_KEY=sk-xxx

Set default per app:
    getv use prellm llm openrouter
    getv use fixpi llm groq
    getv use marksync llm ollama-local

Switch at runtime:
    getv exec llm groq -- python my_script.py
    getv exec llm ollama-local -- python my_script.py
"""

from getv.integrations.litellm import LiteLLMEnv, PROVIDER_KEY_MAP, DEFAULT_MODELS

# --- Check which providers are configured ---

configured = LiteLLMEnv.check_providers()
print("Configured LLM profiles:")
for name, has_model in configured.items():
    status = "✓" if has_model else "✗"
    print(f"  {status} {name}")

# --- Load a specific profile ---

try:
    llm = LiteLLMEnv.from_profile("groq")
    print(f"\nGroq profile:")
    print(f"  Model:    {llm.model}")
    print(f"  Provider: {llm.provider}")
    print(f"  API key:  {'set' if llm.api_key else 'not set'}")

    # Use with litellm:
    # import litellm
    # resp = litellm.completion(**llm.as_completion_kwargs(), messages=[...])

    # Or inject into environment:
    # llm.activate()
    # import litellm
    # resp = litellm.completion(model=llm.model, messages=[...])

except FileNotFoundError:
    print("\nNo 'groq' profile found. Create one:")
    print("  getv set llm groq LLM_MODEL=groq/llama-3.3-70b-versatile GROQ_API_KEY=gsk_xxx")

# --- Available providers and their default models ---

print("\nAll known providers:")
for provider, info in PROVIDER_KEY_MAP.items():
    default = DEFAULT_MODELS.get(provider, "")
    key_var = info.get("key_var", "(no key needed)")
    print(f"  {provider:15s} key={key_var:25s} default={default}")
