# getv — TODO

## Done

- [x] EnvStore — read/write/merge .env files with comment preservation
- [x] ProfileManager — named profiles in directory trees
- [x] Secret detection — is_sensitive_key() with pattern matching
- [x] Masking — mask_value(), mask_dict() for safe display
- [x] Encryption — Fernet encrypt/decrypt for transport
- [x] Format export — JSON, shell, docker, .env, pydantic
- [x] CLI — get/set/list/delete/export/encrypt/decrypt
- [x] 33 unit tests passing
- [x] README, CHANGELOG

## In Progress

- [ ] Integration with fixpi — replace _load_env/_save_env/_load_profiles

## Pending

### Core
- [ ] File watching — auto-reload on .env change (inotify/polling)
- [ ] Validation — required_keys enforcement on profile save
- [ ] Schema — define expected keys/types per category
- [ ] Diff — show changes between profiles or versions

### Security
- [ ] Age encryption support (alternative to Fernet)
- [ ] SOPS integration for team secret management
- [ ] Key rotation — re-encrypt with new key
- [ ] Audit log — track who changed what

### CLI
- [ ] `getv init` — interactive setup wizard
- [ ] `getv copy CATEGORY/SRC CATEGORY/DST` — clone a profile
- [ ] `getv diff CATEGORY A B` — compare two profiles
- [ ] `getv import FILE` — import from docker-compose.yml or .env
- [ ] clickmd integration for rich markdown output

### Integration
- [ ] nfo integration — use getv.security for log redaction
- [ ] PyPI publish
- [ ] GitHub Actions CI


### Implementation
