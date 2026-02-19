## [0.2.2] - 2026-02-19

### Summary

feat(getv): core module improvements

### Other

- update getv/__main__.py


## [0.1.4] - 2026-02-19

### Summary

feat(docs): configuration management system

### Docs

- docs: update README

### Other

- update project.functions.toon
- update project.toon-schema.json


## [0.1.3] - 2026-02-19

### Summary

docs(docs): configuration management system

### Docs

- docs: update README


## [0.1.2] - 2026-02-19

### Summary

docs(docs): configuration management system

### Docs

- docs: update TODO.md


## [0.1.1] - 2026-02-19

### Summary

feat(tests): configuration management system

### Docs

- docs: update README
- docs: update TODO.md

### Test

- update tests/__init__.py
- update tests/test_profile.py
- update tests/test_security.py
- update tests/test_store.py

### Build

- update pyproject.toml

### Config

- config: update goal.yaml

### Other

- update getv/__init__.py
- update getv/__main__.py
- update getv/formats.py
- update getv/profile.py
- update getv/security.py
- update getv/store.py


# Changelog

## [0.1.0] - 2026-02-19

### Added

- **EnvStore** — core `.env` file reader/writer with comment preservation
- **ProfileManager** — named profile management in directory trees (`~/.getv/category/name.env`)
- **Security** — automatic sensitive key detection (`PASSWORD`, `API_KEY`, `TOKEN`, etc.)
- **Masking** — `mask_value()`, `mask_dict()` for safe display/logging
- **Encryption** — Fernet-based `encrypt_store()`/`decrypt_store()` for safe transport
- **Format export** — `to_json()`, `to_shell_export()`, `to_docker_env()`, `to_pydantic_settings()`, `to_pydantic_model()`
- **CLI** — `getv get/set/list/delete/export/encrypt/decrypt` commands
- **Profile merge** — `merge_profiles(base, devices="rpi3", llm="groq")` overlay pattern
- **Search** — `find_by_key()` to locate profiles by variable value
- **Tests** — 33 unit tests covering store, security, and profile management
