# Backend API Reference

## llm_api (http://localhost:8001)

### POST /generate_answer
Request JSON:
```json
{
  "course_id": "string",
  "query": "string",
  "persona": "standard|ki_professor"
}
```

Response JSON:
```json
{
  "answer": "string",
  "images": ["/api/v1/images/...", "..."]
}
```

Notes:
- `persona` is optional and defaults to `standard`.
- `course_id="all"` enables global cross-course retrieval.
- `images` are sanitized and only trusted local paths are returned.

### POST /generate_quiz
Request JSON:
```json
{
  "course_id": "string"
}
```

Response JSON:
```json
{
  "quiz": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer_index": 0,
      "explanation": "string"
    }
  ]
}
```

### POST /generate_presentation
Request JSON:
```json
{
  "course_id": "string",
  "query": "string",
  "persona": "standard|ki_professor"
}
```

Response JSON:
```json
{
  "spoken_text": "string",
  "slides": [
    {
      "title": "string",
      "bullets": ["string", "string", "string"],
      "image_url": "/api/v1/images/..."
    },
    {
      "title": "string",
      "bullets": ["string", "string", "string"],
      "image_url": null
    }
  ],
  "images": ["/api/v1/images/...", "..."]
}
```

Notes:
- `slides` is an array (2-4 slides target) and replaces the former single `slide` object contract.
- Each slide object contains:
  - `title`: string
  - `bullets`: array of 3-5 concise bullet fragments
  - `image_url`: one of the provided local image URLs or `null`
- Top-level `images` remains available for compatibility and is restricted to `/api/v1/images/` paths.

## rag_api (http://localhost:8000/api/v1)

### GET /health
Response:
```json
{"status": "healthy"}
```

### POST /courses/{course_id}/documents
Multipart form:
- `week`: int
- `file`: PDF

### GET /courses/{course_id}/documents/{doc_id}/ready
Response shape:
```json
{
  "course_id": "string",
  "doc_id": "string",
  "ready": true,
  "indexed_chunks": 0
}
```

### GET /courses/{course_id}/retrieve
Query params:
- `query` (required)
- `limit` (optional, 1-20)

Notes:
- `course_id="all"` bypasses course filter for global search.
- Retrieval can return `503` if vector DB is unreachable.
