"""Configuration precedence: CLI flag, then SNACKAPP_* env, then snackapp.toml, then default."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

DEFAULTS = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": False,
    "backend_url": None,
    "admin": "on",
    "dev_frontend": False,
}


@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    backend_url: str | None = None
    admin: str = "on"
    dev_frontend: bool = False


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    import tomllib

    data = tomllib.loads(path.read_text())
    return {k: v for k, v in data.items() if k in DEFAULTS}


def _from_env() -> dict[str, Any]:
    out: dict[str, Any] = {}
    mapping: dict[str, tuple[str, Callable[[str], Any]]] = {
        "SNACKAPP_HOST": ("host", str),
        "SNACKAPP_PORT": ("port", int),
        "SNACKAPP_RELOAD": ("reload", lambda v: v.lower() in {"1", "true", "yes", "on"}),
        "SNACKAPP_BACKEND_URL": ("backend_url", str),
        "SNACKAPP_ADMIN": ("admin", str),
        "SNACKAPP_DEV_FRONTEND": (
            "dev_frontend",
            lambda v: v.lower() in {"1", "true", "yes", "on"},
        ),
    }
    for env, (key, caster) in mapping.items():
        raw = os.environ.get(env)
        if raw is None or raw == "":
            continue
        out[key] = caster(raw)
    return out


def resolve(
    *,
    cli: dict[str, Any] | None = None,
    env: dict[str, Any] | None = None,
    toml_path: Path | None = None,
) -> Settings:
    """Resolve settings. CLI wins, then env, then TOML, then defaults."""
    merged: dict[str, Any] = dict(DEFAULTS)
    toml_data = _load_toml(toml_path or Path("snackapp.toml"))
    merged.update({k: v for k, v in toml_data.items() if v is not None})
    env_data = env if env is not None else _from_env()
    merged.update({k: v for k, v in env_data.items() if v is not None})
    if cli:
        merged.update({k: v for k, v in cli.items() if v is not None})
    names = {f.name for f in fields(Settings)}
    return Settings(**{k: v for k, v in merged.items() if k in names})
