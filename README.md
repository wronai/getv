# getv — Universal .env Variable Manager

Read, write, encrypt, and delegate environment variables across services and devices.

## Why getv?

Every project reinvents `.env` parsing. `getv` provides one library for:

- **Reading/writing** `.env` files with comment preservation
- **Profile management** — named configs for devices, LLM providers, databases
- **Secret masking** — automatic detection and masking of passwords/keys in logs
- **Encryption** — Fernet-based encryption of sensitive values for safe transport
- **Format export** — dict, JSON, shell, docker-compose, pydantic BaseSettings
- **CLI** — manage profiles from the command line

## Install

```bash
pip install getv                   # core
pip install "getv[crypto]"         # + encryption (Fernet)
pip install "getv[pydantic]"       # + pydantic BaseSettings export
pip install "getv[all]"            # everything
```

## Quick Start

### Python API

```python
from getv import EnvStore, ProfileManager

# Single .env file
store = EnvStore("~/.myapp/.env")
store.set("DB_HOST", "localhost").set("DB_PORT", "5432").save()
print(store.get("DB_HOST"))  # "localhost"

# Profile manager — multiple named configs
pm = ProfileManager("~/.fixpi")
pm.add_category("devices", required_keys=["RPI_HOST", "RPI_USER"])
pm.add_category("llm", required_keys=["LLM_MODEL"])

pm.set("devices", "rpi3", {
    "RPI_HOST": "192.168.1.10",
    "RPI_USER": "pi",
    "RPI_PASSWORD": "secret",
    "RPI_PORT": "22",
})

pm.set("llm", "groq", {
    "LLM_MODEL": "groq/llama-3.3-70b-versatile",
    "GROQ_API_KEY": "gsk_xxx",
})

# Merge profiles on top of base config
base = {"APP_NAME": "fixpi", "RPI_HOST": "default"}
cfg = pm.merge_profiles(base, devices="rpi3", llm="groq")
# cfg["RPI_HOST"] == "192.168.1.10" (overridden by device profile)
# cfg["LLM_MODEL"] == "groq/llama-3.3-70b-versatile"
```

### CLI

```bash
# Set variables
getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PASSWORD=secret

# Get a single variable
getv get devices rpi3 RPI_HOST
# → 192.168.1.10

# List all categories
getv list
#   devices/ (2 profiles)
#   llm/ (3 profiles)

# List profiles in a category (secrets masked)
getv list devices
#   rpi3: RPI_HOST=192.168.1.10, RPI_USER=pi, RPI_PASSWORD=secr***

# Show all variables (unmasked)
getv list devices rpi3 --show-secrets

# Export to different formats
getv export devices rpi3 --format json
getv export devices rpi3 --format shell
getv export devices rpi3 --format pydantic
getv export llm groq --format docker

# Encrypt sensitive values (Fernet)
getv encrypt devices rpi3
# → Generated key: ~/.getv/.fernet.key
# → Encrypted sensitive values in devices/rpi3

# Decrypt
getv decrypt devices rpi3

# Delete a profile
getv delete devices old-rpi
```

## Profile Directory Structure

```
~/.getv/                    ← GETV_HOME (configurable)
├── .fernet.key             ← encryption key (chmod 600)
├── devices/
│   ├── rpi3.env
│   ├── rpi4-prod.env
│   └── rpi5-kiosk.env
└── llm/
    ├── groq.env
    ├── openrouter.env
    └── ollama.env
```

Each `.env` file is a standard `KEY=VALUE` file:

```bash
# ~/.getv/devices/rpi3.env
RPI_HOST=192.168.1.10
RPI_USER=pi
RPI_PASSWORD=secret
RPI_PORT=22
```

## Security

### Automatic Secret Detection

Keys matching these patterns are automatically masked in display/logs:

`PASSWORD`, `PASSWD`, `SECRET`, `TOKEN`, `API_KEY`, `APIKEY`,
`PRIVATE_KEY`, `ACCESS_KEY`, `ACCESS_TOKEN`, `AUTH`, `CREDENTIAL`

```python
from getv.security import mask_dict, is_sensitive_key

data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret123"}
print(mask_dict(data))
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secr***"}
```

### Encryption for Transport

```python
from getv.security import generate_key, encrypt_store, decrypt_store

key = generate_key()
data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
encrypted = encrypt_store(data, key, only_sensitive=True)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "ENC:gAAA..."}

original = decrypt_store(encrypted, key)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
```

## Format Export

| Format | Function | Output |
|--------|----------|--------|
| dict | `store.as_dict()` | `{"KEY": "val"}` |
| JSON | `to_json(data)` | `{"KEY": "val"}` |
| Shell | `to_shell_export(data)` | `export KEY='val'` |
| Docker | `to_docker_env(data)` | `KEY=val` |
| .env | `to_env_file(data)` | `KEY=val` |
| Pydantic | `to_pydantic_settings(data)` | Python class source |
| Pydantic model | `to_pydantic_model(data)` | BaseSettings instance |

## Integration with fixpi

`getv` powers fixpi's device and LLM profile management:

```python
from getv import ProfileManager

pm = ProfileManager("~/.fixpi")
pm.add_category("devices")
pm.add_category("llm")

# fixpi delegates all .env operations to getv
cfg = pm.merge_profiles(base_env, devices="rpi3", llm="groq")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GETV_HOME` | `~/.getv` | Base directory for profiles |

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
