"""Multi-file page discovery.

A one-file app stays a one-file app. A real one becomes a package:

    myapp/
      app.py            App() + config
      models.py         collections
      pages/
        index.py        -> "/"
        companies.py    -> "/companies"
        companies/
          index.py      -> "/companies"
          [id].py       -> "/companies/{id}"
        settings/
          team.py       -> "/settings/team"
      actions/
        deals.py

Page modules never import the app object -- they use the module-level `@page`
and `@action` decorators, which bind to whichever app is being loaded. That
keeps `app.py -> pages/ -> app.py` from becoming a circular import.
"""
from __future__ import annotations

import contextvars
import importlib.util
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# The app currently being loaded; set by App.autodiscover().
_loading: contextvars.ContextVar[Any] = contextvars.ContextVar("sa_loading_app")


class NoAppLoadingError(RuntimeError):
    pass


def _current() -> Any:
    app = _loading.get(None)
    if app is None:
        raise NoAppLoadingError(
            "@page/@action used outside app loading. Either decorate with "
            "`@app.page(...)` directly, or put the module under the pages/ "
            "directory passed to App(pages=...)."
        )
    return app


def page(path: str | None = None, *, title: str = "", nav: bool = False,
         icon: str | None = None, order: int = 0) -> Callable:
    """Register a page. `path` defaults to the route derived from the filename."""
    def deco(fn: Callable) -> Callable:
        app = _current()
        mod = sys.modules.get(fn.__module__)
        route = path or getattr(mod, "__sa_route__", None)
        if route is None:
            raise ValueError(f"{fn.__name__}: no path given and no route could be derived")
        app.page(route, title=title or _titleize(fn.__name__), nav=nav,
                 icon=icon, order=order)(fn)
        return fn
    return deco


def action(fn: Callable) -> Callable:
    """Register an action from anywhere under the app package."""
    return _current().action(fn)


def _titleize(name: str) -> str:
    return name.replace("_", " ").strip().title()


def route_from_path(rel: Path) -> str:
    """pages/companies/[id].py -> /companies/{id}; pages/index.py -> /"""
    parts = list(rel.parts)
    parts[-1] = parts[-1][: -len(".py")]
    if parts[-1] == "index":
        parts.pop()
    segs = []
    for p in parts:
        m = re.fullmatch(r"\[(\w+)\]", p)
        segs.append(f"{{{m.group(1)}}}" if m else p)
    return "/" + "/".join(segs) if segs else "/"


def _package_of(path: Path) -> str:
    """Walk up while __init__.py exists to recover the real dotted package name."""
    parts: list[str] = []
    cur = path
    while (cur / "__init__.py").exists():
        parts.append(cur.name)
        cur = cur.parent
    return ".".join(reversed(parts))


def _module_name(pkg: str, rel: Path) -> str:
    """Route params are bracketed, which is not a legal identifier -- sanitise."""
    segs = [re.sub(r"\W", "_", p) for p in rel.with_suffix("").parts]
    return ".".join(filter(None, [pkg, *segs]))


def load_package(app: Any, root: Path, kind: str = "pages") -> list[str]:
    """Import every module under `root`, binding decorators to `app`.

    Modules are registered under their true dotted package name so ordinary
    relative imports (`from ..models import deals`) work exactly as they would
    anywhere else in the package.
    """
    loaded: list[str] = []
    if not root.exists():
        return loaded

    # pages/ and actions/ need not be packages themselves; their parent is.
    if (root / "__init__.py").exists():
        pkg = _package_of(root)
    else:
        parent = _package_of(root.parent)
        pkg = f"{parent}.{root.name}" if parent else root.name

    token = _loading.set(app)
    try:
        for file in sorted(root.rglob("*.py")):
            if file.name.startswith("_"):
                continue
            rel = file.relative_to(root)
            default_route = route_from_path(rel) if kind == "pages" else None
            mod_name = _module_name(pkg, rel)

            spec = importlib.util.spec_from_file_location(mod_name, file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            setattr(module, "__sa_route__", default_route)
            # __package__ is what relative imports resolve against.
            module.__package__ = mod_name.rsplit(".", 1)[0]
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            loaded.append(f"{rel} -> {default_route}" if default_route else str(rel))
    finally:
        _loading.reset(token)
    return loaded
