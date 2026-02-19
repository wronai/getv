"""Export .env data to various formats — dict, JSON, shell, pydantic."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type


def to_dict(data: Dict[str, str]) -> Dict[str, str]:
    """Identity — return a plain dict copy."""
    return dict(data)


def to_json(data: Dict[str, str], indent: int = 2) -> str:
    """Export as formatted JSON string."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def to_shell_export(data: Dict[str, str]) -> str:
    """Generate shell `export KEY='value'` statements."""
    lines = []
    for key, value in sorted(data.items()):
        escaped = value.replace("'", "'\\''")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines)


def to_docker_env(data: Dict[str, str]) -> str:
    """Generate docker-compose environment format (KEY=value)."""
    return "\n".join(f"{k}={v}" for k, v in sorted(data.items()))


def to_env_file(data: Dict[str, str], header: Optional[str] = None) -> str:
    """Generate .env file content with optional header comment."""
    lines = []
    if header:
        lines.append(f"# {header}")
        lines.append("")
    for key, value in data.items():
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def to_pydantic_settings(data: Dict[str, str], class_name: str = "Settings") -> str:
    """Generate a pydantic BaseSettings class source code from env data.

    Returns Python source code string that can be written to a file.
    """
    lines = [
        "from pydantic_settings import BaseSettings",
        "",
        "",
        f"class {class_name}(BaseSettings):",
    ]
    for key, value in data.items():
        # Infer type from value
        field_name = key.lower()
        if value.isdigit():
            lines.append(f"    {field_name}: int = {value}")
        elif value.lower() in ("true", "false"):
            lines.append(f'    {field_name}: bool = {value.capitalize()}')
        else:
            lines.append(f'    {field_name}: str = "{value}"')
    lines.append("")
    lines.append("    class Config:")
    lines.append('        env_file = ".env"')
    lines.append("")
    return "\n".join(lines)


def to_pydantic_model(data: Dict[str, str], class_name: str = "Settings") -> Any:
    """Create an actual pydantic BaseSettings instance from env data.

    Requires pydantic and pydantic-settings to be installed.
    Returns a BaseSettings instance.
    """
    try:
        from pydantic_settings import BaseSettings
        from pydantic import Field
    except ImportError:
        raise ImportError("Install getv[pydantic]: pip install getv[pydantic]")

    # Build fields dict for dynamic model creation
    fields: Dict[str, Any] = {}
    for key, value in data.items():
        field_name = key.lower()
        if value.isdigit():
            fields[field_name] = (int, int(value))
        elif value.lower() in ("true", "false"):
            fields[field_name] = (bool, value.lower() == "true")
        else:
            fields[field_name] = (str, value)

    # Create dynamic model
    from pydantic import create_model
    Model = create_model(
        class_name,
        __base__=BaseSettings,
        **{k: (t, d) for k, (t, d) in fields.items()},
    )
    return Model()
