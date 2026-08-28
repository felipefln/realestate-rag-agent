# realestate-rag-agent

Agente de IA para busca inteligente de imóveis (venda e locação), com RAG, GraphRAG e
orquestração via LangGraph/Bedrock Agents. Backend em FastAPI com guardrails de segurança
e exposição via MCP.

> A base de dados é um dataset sintético de imóveis de Florianópolis — o projeto não faz
> scraping de plataformas de imóveis.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · FastAPI · SQLAlchemy 2 + Alembic ·
Postgres/pgvector · sentence-transformers · pydantic-settings · Ruff · Pytest · Docker

## Rodando

```bash
make install    # uv sync
make db-up      # sobe o Postgres (pgvector) via Docker
make migrate    # alembic upgrade head
make seed       # popula o banco com o dataset sintético
make embed      # gera os embeddings das descrições (pgvector)
make dev        # uvicorn com --reload
```

App em http://localhost:8000 — docs em `/docs`, healthcheck em `/health`.

Config via variáveis `APP_*` (veja `.env.example`). Embeddings: `APP_EMBEDDING_PROVIDER`
= `local` (padrão, sentence-transformers multilíngue, 384 dims, sem API key), `openai`
(`text-embedding-3-small`, precisa de `APP_OPENAI_API_KEY`) ou `fake` (testes).
Trocar de provider com dimensão diferente exige nova migration da coluna `embedding`.

Testes: `make test` roda tudo; `make test-fast` pula o baseline de qualidade (`-m "not slow"`),
que carrega o modelo real.

### Docker

```bash
make docker-up      # sobe db + api (roda as migrations no boot)
make docker-down
```

## Endpoints

| método | rota | descrição |
|--------|------|-----------|
| `GET` | `/health` | healthcheck |
| `GET` | `/search` | busca semântica: `?q=<linguagem natural>` + mesmos filtros estruturados, retorna itens com `score` |
| `GET` | `/properties` | lista com filtros (`operation`, `neighborhood`, `min_price`, `max_price`, `min_bedrooms`, ...) e paginação |
| `GET` | `/properties/{id}` | detalhe |
| `POST` | `/properties` | cria |
| `PATCH` | `/properties/{id}` | atualiza |
| `DELETE` | `/properties/{id}` | remove |

## Estrutura

```
src/realestate_rag_agent/
├── api/           # routers FastAPI + schemas (health, properties, search)
├── core/          # config, conexão com o banco
├── services/      # regras de negócio, embeddings, busca semântica
└── repositories/  # models SQLAlchemy e acesso a dados (incl. busca vetorial)
migrations/        # Alembic
scripts/           # geração/seed do dataset e dos embeddings
data/              # dataset sintético versionado (properties.json)
tests/baseline/    # casos pergunta → expectativa da busca semântica
```
