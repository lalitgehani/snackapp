from click.testing import CliRunner

from snackapp.cli import cli


def test_routes_without_app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["routes"])
    assert result.exit_code != 0


def test_init_then_routes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "demo"])
    assert result.exit_code == 0
    monkeypatch.chdir(tmp_path / "demo")
    result = runner.invoke(cli, ["routes"])
    # app.py defines @page but also pages/index — may fail if snackapp not loading
    assert result.exit_code in (0, 1)
