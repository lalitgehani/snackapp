# Deploying SnackApp

## Single process with SQLite

```bash
pip install snackapp
snackapp init myapp && cd myapp
snackapp run --host 0.0.0.0 --port 8000
```

## PostgreSQL

Set `SNACKBASE_DATABASE_URL=postgresql+asyncpg://user:pass@host/db` before
`snackapp run`. Keep `.snackapp/secret.key` mode 0600.

## Docker

See the repository `Dockerfile`. Build the wheel first (`uv build`), then
`docker build`.

## Trusted publishing

Neither repository stores a PyPI token. On tag `v*`, GitHub Actions uses
OIDC (`id-token: write`) with `pypa/gh-action-pypi-publish`.

Before the first tag, an owner must:

1. Create the PyPI projects `snackbase` then `snackapp` (or claim the names).
2. Add a trusted publisher: GitHub org/user, repository, workflow `publish.yml`,
   environment `pypi`.
3. Tag and push `v0.12.0` on SnackBase, then `v0.1.0` on snackapp.
