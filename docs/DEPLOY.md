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
