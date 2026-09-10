"""Public exceptions."""

from __future__ import annotations


class ValidationError(Exception):
    """Raised by an action to surface a message without re-rendering the page."""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.message = message
        self.field = field
        super().__init__(message)


class DuplicateRouteError(RuntimeError):
    """Two modules declared the same route."""


class UnknownRevisionError(RuntimeError):
    """The database is at a migration revision this binary does not know."""


class DestructiveChangeError(RuntimeError):
    """Schema sync hit a destructive change and needs ``snackapp migrate --confirm``."""
