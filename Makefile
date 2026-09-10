.PHONY: build-frontend test

build-frontend:
	cd frontend && npm ci && npm run build
	rm -rf src/snackapp/static/assets
	mkdir -p src/snackapp/static/assets
	cp -R frontend/dist/. src/snackapp/static/

test:
	uv run ruff check .
	uv run mypy src/
	uv run pytest --cov
