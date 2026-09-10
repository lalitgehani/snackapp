from pathlib import Path

from snackapp.app import route_specificity
from snackapp.discovery import route_from_path


def test_route_from_path_index():
    assert route_from_path(Path("index.py")) == "/"


def test_route_from_path_param():
    assert route_from_path(Path("companies/[id].py")) == "/companies/{id}"


def test_static_beats_parameterized():
    paths = ["/companies/{id}", "/companies"]
    ordered = sorted(paths, key=route_specificity)
    assert ordered[0] == "/companies"
