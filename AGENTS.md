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
