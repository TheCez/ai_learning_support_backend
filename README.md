# ai_learning_support_backend

Backend monorepo containing:

- `ai-learning-support-rag-api` (RAG ingestion/retrieval API)
- `llm_api` (LLM answer-generation API)

## Quick Start (Unified Docker)

The root compose file launches both APIs and Qdrant together.

### 1) Create env files

From the repository root:

```bash
cp ai-learning-support-rag-api/.env.example ai-learning-support-rag-api/.env
cp llm_api/.env.example llm_api/.env
```

Then fill required values in both `.env` files.

### 2) Launch all services

```bash
docker compose up --build
```

Run detached if preferred:

```bash
docker compose up --build -d
```

### 3) Verify services

- RAG API health: `http://localhost:8000/api/v1/health`
- RAG test UI: `http://localhost:8000/api/v1/rag-test-app`
- LLM API docs: `http://localhost:8001/docs`
- Qdrant: `http://localhost:6333/collections`

## Service Ports

- `8000` -> `rag_api`
- `8001` -> `llm_api`
- `6333` -> `qdrant`

## Useful Commands

Stop services:

```bash
docker compose down
```

Stop and remove volumes:

```bash
docker compose down -v
```

Rebuild from scratch:

```bash
docker compose build --no-cache
docker compose up
```