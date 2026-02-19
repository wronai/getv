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
        clickmd.echo(f"\033[31m❌ Profile not found: {category}/{profile}\033[0m", err=True)
        
        # Show helpful suggestions
        existing_profiles = pm.list_names(category)
        
        if existing_profiles:
            clickmd.echo(f"\n\033[33m💡 Available {category} profiles:\033[0m", err=True)
            for name in existing_profiles:
                clickmd.echo(f"  • {name}", err=True)
            clickmd.echo(f"\n\033[32m➡️  Try: getv get {category} {existing_profiles[0]} KEY\033[0m", err=True)
        else:
            clickmd.echo(f"\n\033[33m💡 No {category} profiles found. Create one first:\033[0m", err=True)
            clickmd.echo("\n\033[32m➡️  Example:\033[0m", err=True)
            clickmd.echo(f"   getv set {category} {profile} KEY=value", err=True)
        
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
        clickmd.echo(f"\033[31m❌ Profile not found: {category}/{profile}\033[0m", err=True)
        
        # Show helpful suggestions
        existing_profiles = pm.list_names(category)
        
        if existing_profiles:
            clickmd.echo(f"\n\033[33m💡 Available {category} profiles:\033[0m", err=True)
            for name in existing_profiles:
                clickmd.echo(f"  • {name}", err=True)
            clickmd.echo(f"\n\033[32m➡️  Try: getv list {category} {existing_profiles[0]}\033[0m", err=True)
        else:
            clickmd.echo(f"\n\033[33m💡 No {category} profiles found. Create one first:\033[0m", err=True)
            clickmd.echo("\n\033[32m➡️  Example:\033[0m", err=True)
            clickmd.echo(f"   getv set {category} {profile} KEY=value", err=True)
        
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


@cli.command("exec")
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.argument("cmd", nargs=-1, required=True)
@clickmd.pass_context
def exec_cmd(ctx: clickmd.Context, category: str, profile: str, cmd: tuple) -> None:
    """
    ## Run a command with profile env vars injected

    ```bash
    getv exec llm groq -- python my_script.py
    getv exec devices rpi3 -- ssh pi@host uname -a
    getv exec llm ollama-local -- ollama run llama3.2
    ```
    """
    from getv.integrations.subprocess_env import SubprocessEnv
    import subprocess as sp

    env = SubprocessEnv.build_env(base_dir=ctx.obj["home"], **{category: profile})
    try:
        result = sp.run(list(cmd), env=env)
        raise SystemExit(result.returncode)
    except FileNotFoundError:
        clickmd.echo(f"Command not found: {cmd[0]}", err=True)
        raise SystemExit(127)


@cli.command("use")
@clickmd.argument("app_name")
@clickmd.argument("category")
@clickmd.argument("profile")
@clickmd.pass_context
def use_cmd(ctx: clickmd.Context, app_name: str, category: str, profile: str) -> None:
    """
    ## Set default profile for an application

    ```bash
    getv use fixpi llm groq
    getv use fixpi devices rpi3
    getv use prellm llm openrouter
    getv use marksync llm ollama-local
    ```
    """
    from getv.app_defaults import AppDefaults
    defaults = AppDefaults(app_name, base_dir=ctx.obj["home"])
    defaults.set(category, profile)
    clickmd.echo(f"Default for {app_name}: {category}={profile}")


@cli.command("defaults")
@clickmd.argument("app_name", required=False)
@clickmd.pass_context
def defaults_cmd(ctx: clickmd.Context, app_name: str) -> None:
    """
    ## Show app defaults

    ```bash
    getv defaults              # list all apps with defaults
    getv defaults fixpi        # show fixpi defaults
    ```
    """
    from getv.app_defaults import AppDefaults

    if not app_name:
        apps = AppDefaults.list_apps(base_dir=ctx.obj["home"])
        if not apps:
            clickmd.echo("No app defaults configured. Use: getv use APP CATEGORY PROFILE")
            return
        for name in apps:
            d = AppDefaults(name, base_dir=ctx.obj["home"])
            pairs = ", ".join(f"{k}={v}" for k, v in d.as_dict().items())
            clickmd.echo(f"  {name}: {pairs}")
        return

    d = AppDefaults(app_name, base_dir=ctx.obj["home"])
    data = d.as_dict()
    if not data:
        clickmd.echo(f"No defaults for {app_name}. Use: getv use {app_name} CATEGORY PROFILE")
        return
    for k, v in sorted(data.items()):
        clickmd.echo(f"  {k}={v}")


@cli.command("ssh")
@clickmd.argument("profile")
@clickmd.argument("remote_cmd", required=False, default="")
@clickmd.pass_context
def ssh_cmd(ctx: clickmd.Context, profile: str, remote_cmd: str) -> None:
    """
    ## SSH to a device using its profile

    ```bash
    getv ssh rpi3                    # interactive shell
    getv ssh rpi3 "uname -a"        # run remote command
    ```
    """
    from getv.integrations.ssh import SSHEnv
    import subprocess as sp

    try:
        ssh = SSHEnv.from_profile(profile, base_dir=ctx.obj["home"])
    except FileNotFoundError as e:
        clickmd.echo(f"\033[31m❌ {e}\033[0m", err=True)
        
        # Show helpful suggestions
        from getv.profile import ProfileManager
        pm = ProfileManager(ctx.obj["home"])
        pm.add_category("devices")
        existing_profiles = pm.list_names("devices")
        
        if existing_profiles:
            clickmd.echo("\n\033[33m💡 Available device profiles:\033[0m", err=True)
            for name in existing_profiles:
                clickmd.echo(f"  • {name}", err=True)
            clickmd.echo(f"\n\033[32m➡️  Try: getv ssh {existing_profiles[0]}\033[0m", err=True)
        else:
            clickmd.echo("\n\033[33m💡 No device profiles found. Create one first:\033[0m", err=True)
            clickmd.echo("\n\033[32m➡️  Example:\033[0m", err=True)
            clickmd.echo(f"   getv set devices {profile} RPI_HOST=192.168.1.10 RPI_USER=pi RPI_PASSWORD=your_password", err=True)
            clickmd.echo(f"   getv ssh {profile}", err=True)
        
        raise SystemExit(1)

    cmd = ssh.command(remote_cmd)
    result = sp.run(cmd)
    raise SystemExit(result.returncode)


@cli.command("curl")
@clickmd.argument("profile")
@clickmd.argument("url")
@clickmd.option("-X", "--method", default="GET", help="HTTP method")
@clickmd.option("-d", "--data", "body", default=None, help="Request body")
@clickmd.pass_context
def curl_cmd(ctx: clickmd.Context, profile: str, url: str, method: str, body: str) -> None:
    """
    ## Make authenticated API call using profile credentials

    ```bash
    getv curl groq https://api.groq.com/openai/v1/models
    getv curl openai https://api.openai.com/v1/models
    ```
    """
    from getv.integrations.curl import CurlEnv
    import subprocess as sp

    try:
        c = CurlEnv.from_profile("llm", profile, base_dir=ctx.obj["home"])
    except FileNotFoundError as e:
        clickmd.echo(str(e), err=True)
        raise SystemExit(1)

    cmd = c.command(url, method=method, data=body)
    result = sp.run(cmd)
    raise SystemExit(result.returncode)


@cli.command("grab")
@clickmd.option("--dry-run", is_flag=True, default=False, help="Detect only, don't save")
@clickmd.option("--category", default=None, help="Override category (default: auto-detect)")
@clickmd.option("--provider", default=None, help="Override provider name")
@clickmd.option("--var", "env_var", default=None, help="Override env var name")
@clickmd.option("--no-browser", is_flag=True, default=False, help="Skip browser history check")
@clickmd.pass_context
def grab_cmd(ctx: clickmd.Context, dry_run: bool, category: str,
             provider: str, env_var: str, no_browser: bool) -> None:
    """
    ## Grab API key from clipboard — auto-detect provider and save

    Copy an API key to clipboard, then run:

    ```bash
    getv grab                     # auto-detect and save
    getv grab --dry-run           # detect only
    getv grab --category api      # save to api/ instead of llm/
    getv grab --provider groq     # force provider name
    ```

    ### Supported prefixes (auto-detected)

    `sk-ant-` Anthropic, `sk-` OpenAI, `gsk_` Groq, `sk-or-` OpenRouter,
    `hf_` HuggingFace, `xai-` xAI, `key-` Mistral, `pplx-` Perplexity,
    `nvapi-` NVIDIA, `ghp_` GitHub, `glpat-` GitLab, `SG.` SendGrid,
    `sk_live_`/`sk_test_` Stripe, `AKIA` AWS, and more.

    Falls back to browser history (Chrome/Firefox) if prefix unknown.
    """
    from getv.integrations.clipboard import ClipboardGrab

    grab = ClipboardGrab(check_browser=not no_browser)
    clip = grab.read_clipboard()

    if not clip:
        clickmd.echo("Clipboard is empty. Copy an API key first.", err=True)
        raise SystemExit(1)

    clip = clip.strip()

    if not grab.looks_like_api_key(clip):
        # Still try prefix detection (some keys have special chars)
        prefix_match = grab.detect_by_prefix(clip)
        if not prefix_match:
            clickmd.echo(f"Clipboard doesn't look like an API key: {clip[:20]}...", err=True)
            raise SystemExit(1)

    result = grab.detect(clip)
    if result is None:
        clickmd.echo("Could not detect API key in clipboard.", err=True)
        raise SystemExit(1)

    # Apply user overrides
    if provider:
        result.provider = provider
    if env_var:
        result.env_var = env_var
    if category:
        result.category = category

    # Handle undetected — prompt for provider
    if result.source == "undetected" and not provider:
        clickmd.echo(f"Key detected ({clip[:8]}...) but provider unknown.")
        result.provider = clickmd.prompt("Provider name (e.g. groq, openai)")
        result.env_var = clickmd.prompt("Env var name (e.g. GROQ_API_KEY)",
                                         default=f"{result.provider.upper()}_API_KEY")
        result.source = "manual"

    # Display
    source_label = {"prefix": "Prefix match", "browser": "Browser history",
                    "manual": "User input"}.get(result.source, result.source)

    clickmd.echo(f"Detected:  {result.provider} ({result.env_var})")
    clickmd.echo(f"Key:       {result.masked_key}")
    clickmd.echo(f"Source:    {source_label}")
    if result.domain:
        clickmd.echo(f"Domain:    {result.domain}")
    clickmd.echo(f"Category:  {result.category}")
    clickmd.echo(f"Profile:   ~/.getv/{result.category}/{result.provider}.env")

    if dry_run:
        clickmd.echo("\n--dry-run: not saving.")
        return

    path = result.save(base_dir=ctx.obj["home"])
    clickmd.echo(f"\nSaved to {path}")
    clickmd.echo(f"\nUsage:")
    clickmd.echo(f"  getv get {result.category} {result.provider} {result.env_var}")
    clickmd.echo(f"  getv exec {result.category} {result.provider} -- python app.py")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
