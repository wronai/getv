# Grab — Clipboard API Key Detection

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

## Supported Prefixes (auto-detected)

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

## Detection Priority

1. **Key prefix** — covers ~90% of cases (instant)
2. **Browser history** — Chrome/Firefox SQLite (last 10 min)
3. **User prompt** — fallback

## Python API

```python
from getv.integrations.clipboard import ClipboardGrab

grab = ClipboardGrab()
result = grab.detect()  # reads clipboard, returns GrabResult or None

if result:
    print(result.provider, result.env_var)
    result.save()  # writes to ~/.getv/llm/groq.env
```
