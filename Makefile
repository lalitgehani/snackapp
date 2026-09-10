.PHONY: build-frontend test

build-frontend:
	rm -rf src/snackapp/static/assets
	mkdir -p src/snackapp/static/assets
	cd frontend && npm ci && npm run build

test:
	uv run ruff check .
	uv run mypy src/
	uv run pytest --cov
