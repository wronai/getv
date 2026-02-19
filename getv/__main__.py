"""getv CLI entry point — python -m getv [get|set|list|profile|export]"""

import sys
from pathlib import Path

# Add clickmd dev path if not installed as a package
for _p in [Path(__file__).parents[2] / "contract", Path.home() / "github/wronai/contract"]:
    if (_p / "clickmd").exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
        break

try:
    import clickmd
except ImportError:
    import click as clickmd

from getv.store import EnvStore
from getv.profile import ProfileManager
from getv.security import mask_value, is_sensitive_key, mask_dict


def _default_manager() -> ProfileManager:
    """Create a ProfileManager from GETV_HOME or ~/.getv."""
    import os
    base = os.environ.get("GETV_HOME", "~/.getv")
    pm = ProfileManager(base)
    # Auto-discover existing categories from subdirectories
    base_path = Path(base).expanduser().resolve()
    if base_path.exists():
        for d in sorted(base_path.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                pm.add_category(d.name)
    return pm


@clickmd.group(invoke_without_command=True)
@clickmd.version_option("0.1.0", prog_name="getv")
@clickmd.option("--home", "home_dir", default=None, envvar="GETV_HOME",
                help="Base directory for profiles (default: ~/.getv)")
@clickmd.pass_context
def cli(ctx: clickmd.Context, home_dir: str) -> None:
    """
    # getv — Universal .env Variable Manager

    Read, write, list, and manage environment variables across services and devices.

    ## Quick Start

    ```bash
    getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi
    getv get devices rpi3 RPI_HOST
    getv list devices
    getv export devices rpi3 --format json
    ```
    """
    ctx.ensure_object(dict)
    ctx.obj["home"] = home_dir or "~/.getv"
    if ctx.invoked_subcommand is None:
        clickmd.echo(ctx.get_help())


@cli.command()
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.argument("key")
@clickmd.pass_context
def get(ctx: clickmd.Context, category: str, profile: str, key: str) -> None:
    """
    ## Get a variable

    ```bash
    getv get devices rpi3 RPI_HOST
    ```
    """
    pm = ProfileManager(ctx.obj["home"])
    store = pm.get(category, profile)
    if store is None:
        clickmd.echo(f"Profile not found: {category}/{profile}", err=True)
        raise SystemExit(1)
    value = store.get(key)
    if value is None:
        clickmd.echo(f"Key not found: {key}", err=True)
        raise SystemExit(1)
    clickmd.echo(value)


@cli.command("set")
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.argument("pairs", nargs=-1, required=True)
@clickmd.pass_context
def set_cmd(ctx: clickmd.Context, category: str, profile: str, pairs: tuple) -> None:
    """
    ## Set variables

    ```bash
    getv set devices rpi3 RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PORT=22
    ```
    """
    pm = ProfileManager(ctx.obj["home"])
    pm.add_category(category)
    data = {}
    for pair in pairs:
        if "=" not in pair:
            clickmd.echo(f"Invalid format: {pair} (expected KEY=VALUE)", err=True)
            raise SystemExit(1)
        k, _, v = pair.partition("=")
        data[k.strip()] = v.strip()

    store = pm.set(category, profile, data)
    clickmd.echo(f"Saved {len(data)} var(s) to {store.path}")


@cli.command("list")
@clickmd.argument("category", required=False)
@clickmd.argument("profile", required=False)
@clickmd.option("--show-secrets", is_flag=True, default=False, help="Show unmasked sensitive values")
@clickmd.pass_context
def list_cmd(ctx: clickmd.Context, category: str, profile: str, show_secrets: bool) -> None:
    """
    ## List profiles or variables

    ```bash
    getv list                          # all categories
    getv list devices                  # all device profiles
    getv list devices rpi3             # variables in rpi3
    getv list devices rpi3 --show-secrets
    ```
    """
    pm = ProfileManager(ctx.obj["home"])
    base = Path(ctx.obj["home"]).expanduser().resolve()

    if not category:
        # List categories
        if base.exists():
            cats = [d.name for d in sorted(base.iterdir()) if d.is_dir() and not d.name.startswith(".")]
            if cats:
                for c in cats:
                    count = len(list((base / c).glob("*.env")))
                    clickmd.echo(f"  {c}/ ({count} profiles)")
            else:
                clickmd.echo(f"No categories in {base}")
        else:
            clickmd.echo(f"Directory not found: {base}")
        return

    if not profile:
        # List profiles in category
        pm.add_category(category)
        profiles = pm.list(category)
        if not profiles:
            clickmd.echo(f"No profiles in {category}/")
            return
        for name, store in profiles:
            summary = ", ".join(f"{k}={mask_value(v) if is_sensitive_key(k) and not show_secrets else v}"
                                for k, v in list(store.items())[:3])
            clickmd.echo(f"  {name}: {summary}")
        return

    # Show profile variables
    pm.add_category(category)
    store = pm.get(category, profile)
    if store is None:
        clickmd.echo(f"Profile not found: {category}/{profile}", err=True)
        raise SystemExit(1)
    for k, v in store.items():
        display = v if show_secrets or not is_sensitive_key(k) else mask_value(v)
        clickmd.echo(f"  {k}={display}")


@cli.command()
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.pass_context
def delete(ctx: clickmd.Context, category: str, profile: str) -> None:
    """
    ## Delete a profile

    ```bash
    getv delete devices rpi3
    ```
    """
    pm = ProfileManager(ctx.obj["home"])
    if pm.delete(category, profile):
        clickmd.echo(f"Deleted: {category}/{profile}")
    else:
        clickmd.echo(f"Not found: {category}/{profile}", err=True)


@cli.command("export")
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.option("--format", "fmt", type=clickmd.Choice(["json", "shell", "docker", "env", "pydantic"]),
                default="json", help="Output format")
@clickmd.pass_context
def export_cmd(ctx: clickmd.Context, category: str, profile: str, fmt: str) -> None:
    """
    ## Export profile to different formats

    ```bash
    getv export devices rpi3 --format json
    getv export devices rpi3 --format shell
    getv export devices rpi3 --format pydantic
    getv export llm groq --format docker
    ```
    """
    from getv import formats

    pm = ProfileManager(ctx.obj["home"])
    store = pm.get(category, profile)
    if store is None:
        clickmd.echo(f"Profile not found: {category}/{profile}", err=True)
        raise SystemExit(1)

    data = store.as_dict()
    if fmt == "json":
        clickmd.echo(formats.to_json(data))
    elif fmt == "shell":
        clickmd.echo(formats.to_shell_export(data))
    elif fmt == "docker":
        clickmd.echo(formats.to_docker_env(data))
    elif fmt == "env":
        clickmd.echo(formats.to_env_file(data, header=f"{category}/{profile}"))
    elif fmt == "pydantic":
        class_name = profile.replace("-", "_").title().replace("_", "") + "Settings"
        clickmd.echo(formats.to_pydantic_settings(data, class_name))


@cli.command()
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.option("--key-file", default=None, help="Path to Fernet key file (generated if missing)")
@clickmd.pass_context
def encrypt(ctx: clickmd.Context, category: str, profile: str, key_file: str) -> None:
    """
    ## Encrypt sensitive values in a profile

    ```bash
    getv encrypt devices rpi3
    getv encrypt devices rpi3 --key-file ~/.getv/.fernet.key
    ```
    """
    from getv.security import encrypt_store, generate_key

    pm = ProfileManager(ctx.obj["home"])
    store = pm.get(category, profile)
    if store is None:
        clickmd.echo(f"Profile not found: {category}/{profile}", err=True)
        raise SystemExit(1)

    # Load or generate key
    key_path = Path(key_file) if key_file else Path(ctx.obj["home"]).expanduser() / ".fernet.key"
    key_path = key_path.expanduser().resolve()
    if key_path.exists():
        key = key_path.read_bytes().strip()
    else:
        key = generate_key()
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)
        key_path.chmod(0o600)
        clickmd.echo(f"Generated key: {key_path}")

    encrypted = encrypt_store(store.as_dict(), key, only_sensitive=True)
    store.update(encrypted)
    store.save()
    clickmd.echo(f"Encrypted sensitive values in {category}/{profile}")


@cli.command()
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.option("--key-file", default=None, help="Path to Fernet key file")
@clickmd.pass_context
def decrypt(ctx: clickmd.Context, category: str, profile: str, key_file: str) -> None:
    """
    ## Decrypt encrypted values in a profile

    ```bash
    getv decrypt devices rpi3
    ```
    """
    from getv.security import decrypt_store

    pm = ProfileManager(ctx.obj["home"])
    store = pm.get(category, profile)
    if store is None:
        clickmd.echo(f"Profile not found: {category}/{profile}", err=True)
        raise SystemExit(1)

    key_path = Path(key_file) if key_file else Path(ctx.obj["home"]).expanduser() / ".fernet.key"
    key_path = key_path.expanduser().resolve()
    if not key_path.exists():
        clickmd.echo(f"Key file not found: {key_path}", err=True)
        raise SystemExit(1)

    key = key_path.read_bytes().strip()
    decrypted = decrypt_store(store.as_dict(), key)
    store.update(decrypted)
    store.save()
    clickmd.echo(f"Decrypted values in {category}/{profile}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
