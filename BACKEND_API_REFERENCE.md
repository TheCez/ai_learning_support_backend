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
  "slides": [
    {
      "title": "string",
      "bullets": ["string", "string", "string"],
      "image_url": "/api/v1/images/...",
      "spoken_text": "The narration for this specific slide...",
      "source_page": 6
    },
    {
      "title": "string",
      "bullets": ["string", "string", "string"],
      "image_url": null,
      "spoken_text": "The narration for this second slide...",
      "source_page": null
    }
  ],
  "images": ["/api/v1/images/...", "..."]
}
```

Notes:
- `slides` is an array of 2-4 slides, each with its own narration.
- Each slide object contains:
  - `title`: string (3-10 words)
  - `bullets`: array of 3-5 concise bullet fragments (4-7 words each)
  - `image_url`: one of the provided local image URLs or `null`
  - `spoken_text`: the specific narration/script for Prof. Wagner to say while this slide is displayed (1-2 sentences)
  - `source_page`: primary PDF page number (`int`) used for that slide, or `null` when unavailable
- Top-level `images` contains all relevant images across the presentation, restricted to `/api/v1/images/` paths.
- Per-slide `spoken_text` enables accurate audio synchronization with slide transitions.

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
