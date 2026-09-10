# SnackApp

A Python application framework with SnackBase embedded. One install, one command, a working multi-user app.

```bash
pip install snackapp
snackapp init demo
cd demo
snackapp run
```

Open http://localhost:8000 and log in with the credentials printed on first boot.

![SnackApp home after first login](docs/quickstart.png)

See `examples/crm` for a Twenty-inspired CRM built only on the public API.

## Versioning

SnackApp is `0.1.0`. Before `1.0`, breaking changes may appear in minor releases. Pin `snackapp~=0.1` if you need a freeze.

## Publishing

CI publishes to PyPI from a `v*` tag using [trusted publishing](https://docs.pypi.org/trusted-publishers/) (`id-token: write`, no API token in the repo). Publish `snackbase` first, then `snackapp`. Configure the PyPI trusted publisher for `.github/workflows/publish.yml` before pushing a tag.

## Docs

- Install, tutorial, `ui.*`, field types: `docs/` in this repo and [SnackApp in the SnackBase docs](https://docs.snackbase.dev/guides/snackapp) once published
- Deployment: [`docs/DEPLOY.md`](docs/DEPLOY.md)
