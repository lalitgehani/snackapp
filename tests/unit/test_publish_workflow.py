"""Trusted publishing uses OIDC, never a static PyPI token."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"
TEST_WORKFLOW = ROOT / ".github" / "workflows" / "test.yml"
README = ROOT / "README.md"
DEPLOY = ROOT / "docs" / "DEPLOY.md"


def test_publish_workflow_uses_oidc_and_no_token_secret():
    text = WORKFLOW.read_text()
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish" in text
    assert "PYPI_API_TOKEN" not in text
    assert "TWINE_PASSWORD" not in text
    assert "password:" not in text.lower() or "id-token" in text


def test_ci_installs_from_testpypi_on_os_matrix():
    text = TEST_WORKFLOW.read_text()
    assert "install-testpypi" in text
    assert "test.pypi.org/simple/" in text
    assert "--only-binary=:all:" in text
    assert "snackapp==0.1.1" in text
    assert "snackbase==0.12.1" in text
    assert "ubuntu-latest" in text
    assert "macos-latest" in text
    assert "windows-latest" in text
    assert '"3.12"' in text
    assert '"3.13"' in text
    assert "ref: pypi-oidc" in text
    assert "snackbase-0.12.1-py3-none-any.whl" in text
    assert "npm test" in text
    assert "snackapp/frontend" in text


def test_readme_and_deploy_document_testpypi_install():
    readme = README.read_text()
    deploy = DEPLOY.read_text()
    for text in (readme, deploy):
        assert "--extra-index-url https://test.pypi.org/simple/" in text
        assert "--only-binary=:all:" in text
        assert "snackapp==0.1.1" in text
        assert "snackbase==0.12.1" in text
    assert "PYPI_API_TOKEN" not in readme
    assert "pypi-" not in readme.lower()
