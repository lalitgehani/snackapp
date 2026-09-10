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

SnackApp is `0.1.1`. Before `1.0`, breaking changes may appear in minor releases. Pin `snackapp~=0.1` if you need a freeze.

## Publishing

`snackbase 0.12.1` and `snackapp 0.1.1` are on [PyPI](https://pypi.org/project/snackapp/). CI publishes from a `v*` tag using [trusted publishing](https://docs.pypi.org/trusted-publishers/) (`id-token: write`, no API token in the repo). Publish `snackbase` first, then `snackapp`.

PyPI trusted publisher settings:

| Field | snackbase | snackapp |
| --- | --- | --- |
| Owner | `lalitgehani` | `lalitgehani` |
| Repository | `SnackBase` | `snackapp` |
| Workflow | `publish.yml` | `publish.yml` |
| Environment | `pypi` | `pypi` |

Do not push a `v*` tag until those publishers are saved on pypi.org. The first production upload used a local token that is not stored in the repository or in CI.

## Docs

- Install, tutorial, `ui.*`, field types: `docs/` in this repo and [SnackApp in the SnackBase docs](https://docs.snackbase.dev/guides/snackapp)
- Deployment: [`docs/DEPLOY.md`](docs/DEPLOY.md)
