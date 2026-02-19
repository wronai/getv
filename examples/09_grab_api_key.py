#!/usr/bin/env python3
"""getv grab — Auto-detect API keys from clipboard and save to profiles.

Workflow:
    1. Open console.groq.com → generate API key → Ctrl+C
    2. Run: getv grab
    3. Done! Key saved to ~/.getv/llm/groq.env

Detection priority:
    1. Key prefix (gsk_, sk-ant-, sk-or-, ...) — covers ~90% of cases
    2. Browser history (Chrome/Firefox) — last 10 minutes
    3. Ask user — fallback

Supported providers (prefix auto-detection):
    sk-ant-     → Anthropic       ANTHROPIC_API_KEY
    sk-or-      → OpenRouter      OPENROUTER_API_KEY
    sk-/sk-proj → OpenAI          OPENAI_API_KEY
    gsk_        → Groq            GROQ_API_KEY
    hf_         → HuggingFace     HF_API_KEY
    r8_         → Replicate       REPLICATE_API_TOKEN
    xai-        → xAI             XAI_API_KEY
    key-        → Mistral         MISTRAL_API_KEY
    pplx-       → Perplexity      PERPLEXITY_API_KEY
    nvapi-      → NVIDIA          NVIDIA_API_KEY
    ghp_        → GitHub          GITHUB_TOKEN
    glpat-      → GitLab          GITLAB_TOKEN
    SG.         → SendGrid        SENDGRID_API_KEY
    sk_live_    → Stripe          STRIPE_API_KEY
    AKIA        → AWS             AWS_ACCESS_KEY_ID
    dop_v1_     → DigitalOcean    DIGITALOCEAN_TOKEN
    tskey-      → Tailscale       TAILSCALE_API_KEY

CLI usage:
    getv grab                     # auto-detect and save
    getv grab --dry-run           # detect only, don't save
    getv grab --category api      # save to api/ instead of llm/
    getv grab --provider groq     # force provider name
    getv grab --no-browser        # skip browser history check

Python API:
"""

from getv.integrations.clipboard import ClipboardGrab, GrabResult

# --- Auto-detect from clipboard ---

grab = ClipboardGrab(check_browser=True)

# Read clipboard
clip = grab.read_clipboard()
if clip:
    print(f"Clipboard: {clip[:8]}...")

    # Full detection pipeline
    result = grab.detect(clip)
    if result:
        print(f"Provider:  {result.provider}")
        print(f"Env var:   {result.env_var}")
        print(f"Category:  {result.category}")
        print(f"Source:    {result.source}")
        print(f"Key:       {result.masked_key}")

        # Save to profile (uncomment to execute):
        # path = result.save()
        # print(f"Saved to:  {path}")
    else:
        print("Not an API key.")
else:
    print("Clipboard empty.")

# --- Detect specific key (without clipboard) ---

print("\n--- Prefix detection examples ---")
for test_key in [
    "gsk_abc123def456ghi789jkl012345",
    "sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXX",
    "sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXX",
    "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "AKIAIOSFODNN7EXAMPLE12",
]:
    match = ClipboardGrab.detect_by_prefix(test_key)
    if match:
        provider, env_var, domain = match
        print(f"  {test_key[:12]:15s} → {provider:15s} {env_var:25s} {domain}")
