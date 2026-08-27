# realestate-rag-agent

Agente de IA para busca inteligente de imóveis (venda e locação), com RAG, GraphRAG e
orquestração via LangGraph/Bedrock Agents. Backend em FastAPI com guardrails de segurança
e exposição via MCP.

> A base de dados é um dataset sintético/mock — o projeto não faz scraping de plataformas
> de imóveis.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · FastAPI · pydantic-settings · Ruff · Pytest · Docker

## Rodando

```bash
make install    # uv sync
make dev        # uvicorn com --reload
make test       # pytest
make lint       # ruff
```

App em http://localhost:8000 — docs em `/docs`, healthcheck em `/health`.

### Docker

```bash
make docker-up      # http://localhost:8000/health
make docker-down
```

## Estrutura

```
src/realestate_rag_agent/
├── api/           # routers FastAPI
├── core/          # config e infra transversal
├── services/      # lógica de negócio
└── repositories/  # acesso a dados
```
