.PHONY: install dev lint fmt test run docker-build docker-up docker-down

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

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
