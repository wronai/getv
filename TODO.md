# getv — TODO

## Done (v0.1.x)

- [x] EnvStore — read/write/merge .env files with comment preservation
- [x] ProfileManager — named profiles in directory trees
- [x] Secret detection — is_sensitive_key() with pattern matching
- [x] Masking — mask_value(), mask_dict() for safe display
- [x] Encryption — Fernet encrypt/decrypt for transport
- [x] Format export — JSON, shell, docker, .env, pydantic
- [x] CLI — get/set/list/delete/export/encrypt/decrypt
- [x] 33 unit tests passing
- [x] README, CHANGELOG

## Done (v0.2.0)

- [x] Integration with fixpi — replace _load_env/_save_env/_load_profiles
- [x] AppDefaults — per-app default profile selection (~/.getv/defaults/APP.conf)
- [x] Integrations — litellm, ssh, ollama, docker, subprocess, pydantic, curl
- [x] CLI — exec, use, defaults, ssh, curl
- [x] 8 examples in examples/
- [x] Adopted by: fixpi, prellm, code2logic, amen, marksync, curllm
- [x] clickmd integration for rich markdown output
- [x] 84 unit tests

## Done (v0.2.1)

- [x] `getv grab` — clipboard API key auto-detection (19 prefixes, browser history fallback)
- [x] 128 tests (+ 44 clipboard)

## Done (v0.2.2–v0.2.7)

- [x] Validation — required_keys enforcement on profile save (ProfileValidationError)
- [x] `getv diff CATEGORY A B` — compare two profiles (added/removed/changed)
- [x] `getv copy CATEGORY/SRC CATEGORY/DST` — clone a profile (cross-category)
- [x] `getv import FILE` — import from .env or docker-compose.yml
- [x] `getv init` — interactive setup wizard (categories, LLM profile, device profile)
- [x] Key rotation — `rotate_key()` re-encrypts ENC: values from old to new Fernet key
- [x] File watching — `EnvWatcher` with polling, background thread, context manager
- [x] nfo integration — `patch_nfo_redaction()` + `redact_profile_display()` + `profile_env_tagger()`
- [x] GitHub Actions CI (.github/workflows/tests.yml, Python 3.9–3.13)
- [x] 190 tests total (29 E2E CLI + 18 profile + 10 watcher + 3 nfo + 1 rotate_key + existing)

## Pending

### Core

- [ ] Schema — define expected keys/types per category (beyond required_keys)

### Security

- [ ] Age encryption support (alternative to Fernet)
- [ ] SOPS integration for team secret management
- [ ] Audit log — track who changed what

### Integration

- [ ] PyPI publish
