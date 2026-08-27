# realestate-rag-agent

Agente de IA para busca inteligente de imóveis (venda e locação), com RAG, GraphRAG e
orquestração via LangGraph/Bedrock Agents. Backend em FastAPI com guardrails de segurança
e exposição via MCP.

> A base de dados é um dataset sintético de imóveis de Florianópolis — o projeto não faz
> scraping de plataformas de imóveis.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · FastAPI · SQLAlchemy 2 + Alembic ·
Postgres/pgvector · pydantic-settings · Ruff · Pytest · Docker

## Rodando

```bash
make install    # uv sync
make db-up      # sobe o Postgres (pgvector) via Docker
make migrate    # alembic upgrade head
make seed       # popula o banco com o dataset sintético
make dev        # uvicorn com --reload
```

App em http://localhost:8000 — docs em `/docs`, healthcheck em `/health`.

Config via variáveis `APP_*` (veja `.env.example`).

### Docker

```bash
make docker-up      # sobe db + api (roda as migrations no boot)
make docker-down
```

## Endpoints

| método | rota | descrição |
|--------|------|-----------|
| `GET` | `/health` | healthcheck |
| `GET` | `/properties` | lista com filtros (`operation`, `neighborhood`, `min_price`, `max_price`, `min_bedrooms`, ...) e paginação |
| `GET` | `/properties/{id}` | detalhe |
| `POST` | `/properties` | cria |
| `PATCH` | `/properties/{id}` | atualiza |
| `DELETE` | `/properties/{id}` | remove |

## Estrutura

```
src/realestate_rag_agent/
├── api/           # routers FastAPI + schemas
├── core/          # config, conexão com o banco
├── services/      # regras de negócio
└── repositories/  # models SQLAlchemy e acesso a dados
migrations/        # Alembic
scripts/           # geração/seed do dataset
data/              # dataset sintético versionado (properties.json)
```
