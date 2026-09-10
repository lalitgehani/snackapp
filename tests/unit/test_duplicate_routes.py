import pytest

from snackapp.app import App
from snackapp.exceptions import DuplicateRouteError


def test_duplicate_route_names_both_modules():
    app = App("t")

    @app.page("/x")
    def one():
        return None

    with pytest.raises(DuplicateRouteError, match="duplicate route '/x'"):
        @app.page("/x")
        def two():
            return None
