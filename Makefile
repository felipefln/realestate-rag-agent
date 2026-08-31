.PHONY: install dev run lint fmt test test-fast db-up db-down migrate revision seed embed mcp docker-build docker-up docker-down

install:
	uv sync --all-groups

dev: install
	uv run uvicorn realestate_rag_agent.main:app --reload

run:
	uv run uvicorn realestate_rag_agent.main:app --host 0.0.0.0 --port 8000

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -q

test-fast:
	uv run pytest -q -m "not slow"

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"

seed:
	uv run python -m scripts.seed_properties $(ARGS)

embed:
	uv run python -m scripts.embed_properties $(ARGS)

mcp:
	uv run python -m realestate_rag_agent.mcp_server

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
