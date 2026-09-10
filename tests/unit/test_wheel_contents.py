"""The installed package ships the hashed frontend and excludes tests."""

from pathlib import Path

import snackapp


def test_packaged_frontend_has_html_and_hashed_js():
    static = Path(snackapp.__file__).resolve().parent / "static"
    html = static / "index.html"
    assert html.is_file()
    text = html.read_text()
    assert 'id="root"' in text or "id='root'" in text
    assert "<script" in text
    assets = static / "assets"
    js = list(assets.glob("*.js"))
    assert js
    assert not list(assets.glob("*.map"))


def test_package_tree_excludes_tests():
    pkg = Path(snackapp.__file__).resolve().parent
    assert not list(pkg.rglob("test_*.py"))
    assert not list(pkg.rglob("*.map"))
