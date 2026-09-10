"""SnackApp — Python application framework with SnackBase embedded."""

from importlib.metadata import PackageNotFoundError, version

from snackapp import ui
from snackapp.app import App, Ctx, Table
from snackapp.discovery import action, page
from snackapp.schema import Field, Schema, rules_for

try:
    __version__ = version("snackapp")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "App",
    "Ctx",
    "Field",
    "Schema",
    "Table",
    "action",
    "page",
    "rules_for",
    "ui",
    "__version__",
]
