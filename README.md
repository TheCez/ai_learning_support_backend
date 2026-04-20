# AI Learning Support Backend

This repository contains the backend services for the Cura learning platform. It is a backend monorepo that powers document ingestion, retrieval-augmented generation, quiz creation, presentation generation for the avatar-based professor, and additional study support endpoints used by the frontend.

The backend is split into two services:

- `ai-learning-support-rag-api`: ingests course PDFs, extracts and stores content, indexes chunks in Qdrant, and serves retrieval results plus extracted images
- `llm_api`: turns retrieved material into student-facing answers, quizzes, slide-based presentations, flashcards, and library-style study outputs

## Current backend scope

- PDF upload and asynchronous indexing per course
- Retrieval with metadata-based course isolation in a single vector collection
- Extracted image storage and image URL serving
- Grounded answer generation for student questions
- KI-Lehrer presentation generation with multi-slide output, per-slide narration, and optional source-page grounding
- Quiz generation for course content
- Flashcard generation
- Library summary and library card generation
- Docker-based local development with Qdrant included

## Repository structure

```text
ai_learning_support_backend/
|- ai-learning-support-rag-api/
|  |- app/
|  |- tests/
|  |- Dockerfile
|  |- pyproject.toml
|- llm_api/
|  |- app/
|  |- Dockerfile
|  |- pyproject.toml
|- test/
|  |- Anatomy+of+the+Heart.pdf
|- docker-compose.yml
|- BACKEND_API_REFERENCE.md
```

## Architecture

### `rag_api`

The RAG service is a FastAPI application responsible for ingestion and retrieval.

- Accepts PDF uploads per course
- Splits text into chunks with page awareness
- Stores vectors in Qdrant
- Persists raw PDFs and extracted images
- Exposes retrieval endpoints for downstream LLM use
- Serves local extracted images under `/api/v1/images/...`

Key technologies:

- FastAPI
- PyMuPDF
- LangChain text splitters
- FastEmbed
- Qdrant

### `llm_api`

The LLM service is the user-facing AI layer. It calls `rag_api`, synthesizes grounded study responses, and returns frontend-friendly JSON payloads.

- Standard answer generation
- Multi-slide presentation generation for the avatar-based professor
- Quiz generation
- Flashcards
- Library summaries
- Library concept cards

Key technologies:

- FastAPI
- OpenAI-compatible API integration
- `httpx` for internal service calls
- Pydantic v2

## API overview

### `rag_api` base URL

`http://localhost:8000/api/v1`

Important endpoints:

- `GET /health`
- `POST /courses/{course_id}/documents`
- `GET /courses/{course_id}/documents/{doc_id}/ready`
- `GET /courses/{course_id}/retrieve`
- `GET /rag-test-app`
- `GET /images/...`

### `llm_api` base URL

`http://localhost:8001`

Important endpoints:

- `POST /generate_answer`
- `POST /generate_quiz`
- `POST /generate_presentation`
- `POST /generate_flashcards`
- `POST /generate_library_summary`
- `POST /generate_library_cards`

For the exact request and response contracts, see [BACKEND_API_REFERENCE.md](BACKEND_API_REFERENCE.md).

## Quick start

### 1. Create environment files

From the repository root:

```bash
cp ai-learning-support-rag-api/.env.example ai-learning-support-rag-api/.env
cp llm_api/.env.example llm_api/.env
```

Then fill in the required values.

### 2. Start the stack

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up --build -d
```

### 3. Verify services

- RAG API health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- RAG test app: [http://localhost:8000/api/v1/rag-test-app](http://localhost:8000/api/v1/rag-test-app)
- LLM API docs: [http://localhost:8001/docs](http://localhost:8001/docs)
- Qdrant collections: [http://localhost:6333/collections](http://localhost:6333/collections)

## Environment variables

### `ai-learning-support-rag-api/.env`

Important variables include:

- `VECTOR_DB_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_COLLECTION_NAME`
- `RAW_PDF_STORAGE_PATH`
- `EXTRACTED_IMAGE_STORAGE_PATH`
- `EMBEDDING_MODEL`
- `VISION_API_URL`
- `VISION_API_KEY`
- `VISION_MODEL`

### `llm_api/.env`

Important variables include:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `RAG_API_BASE_URL`

The default Docker setup injects `RAG_API_BASE_URL=http://rag_api:8000/api/v1` into `llm_api`.

## Local development notes

- The root `docker-compose.yml` starts `rag_api`, `llm_api`, and `qdrant`
- Qdrant storage is persisted via `./qdrant_storage`
- `uv` is used for dependency management in both backend services
- The included sample PDF in `test/` is useful for ingestion and retrieval testing

## Useful commands

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

## Frontend integration

This backend powers the frontend application in the companion repository:

- Frontend repository: [https://github.com/TheCez/ai-learning-support](https://github.com/TheCez/ai-learning-support)

Integration expectations:

- Frontend uploads PDFs through `rag_api` and polls readiness before study actions
- Frontend uses `llm_api` for student-facing answers and generated learning content
- KI-Lehrer presentation responses return `slides[]` with `title`, `bullets`, `spoken_text`, optional `image_url`, and optional `source_page`
- Image URLs are served from `rag_api` and should be rendered directly by the client
