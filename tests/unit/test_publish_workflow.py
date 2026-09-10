"""Trusted publishing uses OIDC, never a static PyPI token."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"


def test_publish_workflow_uses_oidc_and_no_token_secret():
    text = WORKFLOW.read_text()
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish" in text
    assert "PYPI_API_TOKEN" not in text
    assert "TWINE_PASSWORD" not in text
    assert "password:" not in text.lower() or "id-token" in text
