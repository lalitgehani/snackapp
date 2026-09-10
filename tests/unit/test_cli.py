from importlib.metadata import version

from click.testing import CliRunner

from snackapp.cli import cli


def test_version_matches_metadata():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert version("snackapp") in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SnackApp" in result.output


def test_init_scaffolds_gitignore(tmp_path):
    runner = CliRunner()
    target = tmp_path / "demo"
    result = runner.invoke(cli, ["init", str(target)])
    assert result.exit_code == 0, result.output
    gitignore = (target / ".gitignore").read_text()
    assert ".snackapp/" in gitignore
    assert (target / "app.py").exists()
    assert (target / "pages" / "index.py").exists()
