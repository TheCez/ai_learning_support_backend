# AI Learning Support RAG API - Mission Profile
- **Architecture:** FastAPI (Backend) + Single Vector Database (Multi-Tenant via Metadata) + Local Volume Storage
- **Deployment:** Docker-compose (FastAPI App + Vector DB service)
- **Subagent Roles:** - @dev: Builds the upload and retrieval API endpoints. Implements PDF parsing (e.g., PyMuPDF) and text chunking logic (~1000 characters with 200 overlap). Generates embeddings and strictly enforces attaching metadata (`course_id`, `page_no`, `week`, `doc_id`) to every vector before DB insertion.
  - @ops: Manages Dockerization, configures the single Vector DB container (e.g., Qdrant or ChromaDB), and sets up persistent volume management for both the raw PDF storage and the vector database index.
  - @qa: Writes `pytest` scripts to test API endpoints. Must explicitly test multi-tenant isolation (verifying that metadata filtering works and prevents data leakage between different groups/courses).
- **Rules:** Use `uv` for dependencies. **DO NOT** create multiple databases or collections per course/group; isolate data entirely using metadata filtering in a single collection.

## Current Implementation Status
- Dependency management updated to use `uv` with required ingestion dependencies: `qdrant-client`, `fastembed`, `langchain-text-splitters`, and `pymupdf`.
- Docker setup now runs FastAPI and Qdrant together via `docker-compose`, with Qdrant using the official `qdrant/qdrant` image on port `6333`.
- Qdrant storage now uses a local bind mount at `./qdrant_storage` so the vector database files can be copied between a laptop and a production server.
- Endpoint paths were updated to remove `group_id` from scope:
  - `POST /api/v1/courses/{course_id}/documents`
  - `GET /api/v1/courses/{course_id}/retrieve`
- Metadata schema enforced for vector payloads now strictly uses: `course_id`, `page_no`, `week`, `doc_id`.
- Added Qdrant integration service with collection bootstrap logic that ensures a single `course_materials` collection exists at startup.
- Added page-aware PDF processing using PyMuPDF (`fitz`) and LangChain `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=200`).
- Ingestion endpoint now saves raw PDFs locally and triggers a background ingestion task that chunks page-by-page, embeds with FastEmbed, and upserts vectors with the required metadata payload.
- Qdrant health-check probe is now non-blocking at startup; unreachable Qdrant logs a clear warning and does not crash FastAPI boot.
- Retrieval endpoint is now backed by filtered vector search against `course_materials` with course-level isolation enforced through Qdrant payload filtering.
- Retrieval now returns `503 Service Unavailable` with a clear message when Qdrant is unreachable or a connection error occurs during search.
- The combined test UI is available at `/api/v1/rag-test-app` for uploading PDFs and running raw retrieval queries end-to-end.
- Image-RAG support is being added: extracted PDF images are stored locally, captioned through an OpenAI-compatible Vision API, and indexed in Qdrant with `image_url` metadata.
- Test UI now renders hybrid retrieval results visually: chunks with `image_url` display inline images and Vision-generated captions, while text-only chunks render as standard text cards.
- Text chunks now inherit page-level `image_url` when a page contains extracted images, improving image visibility for text-led queries (e.g., "chambers").
- Added document readiness endpoint `GET /api/v1/courses/{course_id}/documents/{doc_id}/ready`; the test UI now shows a rotating indexing spinner and waits for vector readiness before querying.
- The user-facing demo flow now uses `llm_api` as the only query surface: the Test UI posts `course_id + query` to `llm_api`, which internally fetches RAG results, synthesizes a human-readable answer, and returns only `answer` plus relevant `images`.
- Root `docker-compose.yml` launches both APIs and injects `RAG_API_BASE_URL=http://rag_api:8000/api/v1` into `llm_api` so the demo flow works inside the shared Docker network.

## llm_api Agent Interface (Documented Contract)

### Purpose
- `llm_api` is the user-facing answer synthesis layer.
- It is the only query API the frontend should call for QA-style responses.
- It hides raw retrieval chunks and returns a clean payload for the UI.

### Tech Stack
- FastAPI service (`llm_api/app/main.py`) with CORS enabled for browser clients.
- `openai` Python SDK against an OpenAI-compatible endpoint.
- `httpx` for internal retrieval calls to `rag_api`.
- Pydantic v2 schemas for request/response validation.
- Runtime/dependencies managed with `uv`.

### Public Endpoints
- `POST /generate_answer`
  - Request JSON: `{"course_id": "string", "query": "string", "persona": "standard|ki_professor"}`
  - Special behavior: set `course_id` to `"all"` to query across all indexed courses.
  - Persona behavior: `persona="ki_professor"` switches response style to Prof. Wagner (friendly, encouraging, and more lenient when context is brief).
  - Response JSON: `{"answer": "string", "images": ["string", "..."]}`
- `POST /generate_quiz`
  - Request JSON: `{"course_id": "string"}`
  - Response JSON:
    `{"quiz": [{"question": "string", "options": ["string", "string", "string", "string"], "answer_index": 0, "explanation": "string"}, "..."]}`
  - Target behavior: return up to 10 validated MCQ items.
- `POST /generate_presentation`
  - Request JSON: `{"course_id": "string", "query": "string", "persona": "standard|ki_professor"}`
  - Special behavior: set `course_id` to `"all"` to query across all indexed courses.
  - Persona behavior: `persona="ki_professor"` uses Prof. Wagner answer tone for `spoken_text` before slide summarization.
  - Response JSON: `{"spoken_text": "string", "slide": {"title": "string", "bullets": ["string", "string"]}, "images": ["string", "..."]}`
  - Target behavior: KI-Professor presentation mode—reuses answer generation and summarizes into a single slide with title + bullet points.

### Response Contract for Frontend and Agents
- Output must always be JSON with exactly the top-level fields `answer` and `images`.
- `answer` is a synthesized, student-facing response.
- `images` contains only selected relevant image URLs (not all retrieved images).
- Image safety: image URLs are restricted to trusted local paths and must start with `/api/v1/images/`.
- Raw retrieval chunks/scores must not be exposed by this API.

### Internal Answering Flow
1. Fetch retrieval results from `rag_api`:
   - `GET /api/v1/courses/{course_id}/retrieve?query=...`
  - Reserved keyword: if `course_id` is `"all"`, retrieval runs globally without a `course_id` metadata filter.
2. Generate a concise grounded answer (JSON-only answer payload).
3. Rank image candidates locally using keyword overlap and anatomy-term weighting.
4. Run a second structured model step to choose only the best candidate image IDs.
5. Map selected IDs back to image URLs and return final `{answer, images}`.
6. Fallback behavior:
   - if no retrieval results: return `This was not found in the uploaded material.` with `[]` images.
   - if no image selected: return the top-ranked image as a safe fallback.

### Environment Variables (`llm_api`)
- `OPENAI_API_KEY`: key for OpenAI-compatible provider.
- `OPENAI_BASE_URL`: provider base URL.
- `OPENAI_MODEL`: model name used for both answer and image-selection steps.
- `RAG_API_BASE_URL`: base URL of `rag_api` (default `http://rag_api:8000/api/v1` in Docker network).

### Docker Integration Notes
- `llm_api` is exposed on port `8001`.
- Root compose injects `RAG_API_BASE_URL=http://rag_api:8000/api/v1`.
- Service startup order in root compose ensures `llm_api` depends on `rag_api`.

### Agent Guidance
- Any user query flow should call `llm_api` endpoints first, not raw `/retrieve`, unless debugging retrieval.
- Keep request payload minimal (`course_id`, `query`).
- Preserve strict response shape to avoid frontend regressions.
- If extending features (summary/quiz/multi-turn), maintain backward compatibility for existing `{answer, images}` consumers.

## API Endpoint Reference (Frontend and Agent Contract)

### rag_api (`http://localhost:8000/api/v1`)

| Method | Path | Request Contract | Response Contract | Notes |
|---|---|---|---|---|
| `GET` | `/health` | None | `{"status": "healthy"}` | Health probe for service availability. |
| `POST` | `/courses/{course_id}/documents` | `multipart/form-data` with `week` (int), `file` (PDF) | `{"message": "File uploaded. Ingestion started in background.", "metadata": {"course_id": "...", "week": 1, "doc_id": "...", "file_name": "...", "file_path": "...", "file_size": 12345}}` | Upload starts async ingestion and vector indexing. |
| `GET` | `/courses/{course_id}/documents/{doc_id}/ready` | Path params only | `{"course_id": "...", "doc_id": "...", "ready": true/false, "indexed_chunks": 0}` | Use for polling readiness before querying. |
| `GET` | `/courses/{course_id}/retrieve` | Query params: `query` (string, required), `limit` (int, optional, 1-20, default 5) | `{"results": [{"text": "...", "score": 0.0, "doc_id": "...", "page_no": 1, "week": 1, "image_url": "/api/v1/images/..." | null}]}` | Returns chunk-level retrieval output; `course_id="all"` bypasses course metadata filtering for global search; `503` when vector DB unavailable. |
| `GET` | `/rag-test-app` | None | HTML page | Frontend demo app entrypoint. |
| `GET` | `/retrieve-ui` | None | HTML page | Raw retrieval debug UI. |
| `GET` | `/images/{doc_id}/...` (mounted static under `/api/v1/images`) | None | Image bytes | Use image URLs returned from retrieval/llm_api directly. |

### llm_api (`http://localhost:8001`)

| Method | Path | Request Contract | Response Contract | Notes |
|---|---|---|---|---|
| `POST` | `/generate_answer` | JSON: `{"course_id": "string", "query": "string", "persona": "standard|ki_professor"}` | JSON: `{"answer": "string", "images": ["string", "..."]}` | Primary user-facing QA endpoint; `persona` is optional and defaults to `standard`. |
| `POST` | `/generate_quiz` | JSON: `{"course_id": "string"}` | JSON: `{"quiz": [{"question": "string", "options": ["string", "string", "string", "string"], "answer_index": 0, "explanation": "string"}, "..."]}` | Generates course-grounded quiz set (up to 10 MCQs). |
| `POST` | `/generate_presentation` | JSON: `{"course_id": "string", "query": "string", "persona": "standard|ki_professor"}` | JSON: `{"spoken_text": "string", "slide": {"title": "string", "bullets": ["string", "..."]}, "images": ["string", "..."]}` | KI-Professor presentation mode; `persona` is optional and defaults to `standard`. |

### Error Contract Summary

| Service | Endpoint Pattern | Typical Error | Shape |
|---|---|---|---|
| `rag_api` | retrieval/readiness when vector DB down | `503` | `{"detail": "Vector database is currently unreachable."}` |
| `rag_api` | upload with non-PDF | `400` | `{"detail": "Only PDF files are allowed."}` |
| `llm_api` | schema validation | `422` | FastAPI validation error payload |

### Frontend Integration Rules

- Use `llm_api /generate_answer` for chat-style answer flows.
- Use `llm_api /generate_quiz` for quiz screen flows.
- Use `llm_api /generate_presentation` for KI-Professor presentation mode (single-slide lecture delivery).
- Use `course_id="all"` for global cross-course retrieval in answer/presentation flows when no specific course context is provided.
- Poll `rag_api /courses/{course_id}/documents/{doc_id}/ready` after uploads before enabling ask/quiz/presentation actions.
- Render images from the `images` array as-is; URLs are already routable from `rag_api` static mount.
- Treat `quiz` and presentation `slide` outputs as arrays/objects that may be minimal when indexed material is sparse.
