# Security

## Automatic Secret Detection

Keys matching these patterns are automatically masked in display/logs:

`PASSWORD`, `PASSWD`, `SECRET`, `TOKEN`, `API_KEY`, `APIKEY`,
`PRIVATE_KEY`, `ACCESS_KEY`, `ACCESS_TOKEN`, `AUTH`, `CREDENTIAL`

```python
from getv.security import mask_dict, is_sensitive_key

data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret123"}
print(mask_dict(data))
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secr***"}
```

## Encryption for Transport

```python
from getv.security import generate_key, encrypt_store, decrypt_store

key = generate_key()
data = {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
encrypted = encrypt_store(data, key, only_sensitive=True)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "ENC:gAAA..."}

original = decrypt_store(encrypted, key)
# {"RPI_HOST": "10.0.0.1", "RPI_PASSWORD": "secret"}
```

## Key Rotation

Re-encrypt all values from an old key to a new one:

```python
from getv.security import generate_key, encrypt_store, rotate_key

old_key = generate_key()
new_key = generate_key()

data = {"API_KEY": "sk-secret123"}
encrypted = encrypt_store(data, old_key, only_sensitive=True)

# Rotate to new key
rotated = rotate_key(encrypted, old_key, new_key)
# Now only new_key can decrypt
```

## Validation

Enforce required keys on profile save:

```python
from getv import ProfileManager, ProfileValidationError

pm = ProfileManager("~/.getv")
pm.add_category("devices", required_keys=["RPI_HOST", "RPI_USER"])

try:
    pm.set("devices", "rpi3", {"RPI_HOST": "10.0.0.1"}, validate=True)
except ProfileValidationError as e:
    print(e.missing)  # ["RPI_USER"]
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
