from snackapp.config import resolve


def test_cli_overrides_env_overrides_toml(tmp_path, monkeypatch):
    toml = tmp_path / "snackapp.toml"
    toml.write_text("port = 8000\nhost = 'toml-host'\n")
    monkeypatch.setenv("SNACKAPP_PORT", "9000")
    monkeypatch.setenv("SNACKAPP_HOST", "env-host")
    settings = resolve(cli={"port": 9001}, toml_path=toml)
    assert settings.port == 9001
    assert settings.host == "env-host"


def test_env_overrides_toml(tmp_path, monkeypatch):
    toml = tmp_path / "snackapp.toml"
    toml.write_text("port = 8000\n")
    monkeypatch.setenv("SNACKAPP_PORT", "9000")
    settings = resolve(toml_path=toml)
    assert settings.port == 9000


def test_defaults(tmp_path):
    settings = resolve(toml_path=tmp_path / "missing.toml")
    assert settings.port == 8000
    assert settings.host == "0.0.0.0"
