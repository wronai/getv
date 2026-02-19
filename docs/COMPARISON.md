# Comparison with Similar Tools

## Overview

| Feature | getv | direnv | dotenvx | envie (Rust) |
|---------|------|--------|---------|--------------|
| **Install** | `pip install getv` | `brew install direnv` + hook | `npm i -g @dotenvx/dotenvx` | `cargo install envie` |
| **Set token** | `getv set llm groq KEY=val` | `echo "export KEY=val" > .envrc` | `dotenvx set KEY val` | `envie set KEY val` |
| **Auto-detect** | `getv grab` (clipboard+prefix) | — | — | — |
| **Read token** | `getv get llm groq KEY` | `echo $KEY` (auto-loaded) | `dotenvx get KEY` | `envie get KEY` |
| **Run with env** | `getv exec llm groq -- cmd` | Auto on `cd` | `dotenvx run -- cmd` | `envie load && cmd` |
| **List vars** | `getv list llm` (masks secrets) | — | `dotenvx --all` | `envie get_all` |
| **Profiles** | Categories (llm/devices) + app defaults | Per-folder (.envrc) | Per-file (.env.prod) | Basic (load file) |
| **Integrations** | SSH/curl/Docker/LiteLLM built-in | Shell hooks | Encryption + run | Type-safe Rust lib |

## Detailed Comparison

### getv — most advanced profiles

```bash
getv use fixpi llm groq
getv exec llm groq -- python app.py
getv grab  # auto-detect from clipboard
```

Best for: multi-service setups (RPi + LLM + cloud), homelab, rapid prototyping.

### direnv — automatic per-project

```bash
echo 'export GROQ_API_KEY=gsk_xxx' > .envrc
direnv allow
cd project && python app.py  # auto-load/unload
```

Best for: per-directory environment switching, simple project isolation.

### dotenvx — simple run + encryption

```bash
dotenvx set GROQ_API_KEY gsk_xxx
dotenvx run -f .env.prod -- docker run myapp
```

Best for: encrypted .env files, CI/CD pipelines.

### envie — lightweight Rust/Python

```bash
envie load .env
envie set_system_env GROQ_API_KEY gsk_xxx
```

Best for: Rust projects, type-safe env access.

## Summary

getv wins on **integrations** (SSH, LLM, Docker, clipboard detection) and **profile management** (categories + app defaults). direnv wins on **simplicity** (auto-load on cd). dotenvx on **encryption**. envie on **type safety**.
