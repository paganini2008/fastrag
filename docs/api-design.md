# API Design

Base URL: `/api/v1`

Authentication: `Authorization: Bearer <jwt_token>` or `X-API-Key: <api_key>`

All requests/responses use `Content-Type: application/json`.

---

## Authentication

### POST /api/v1/auth/login
```json
// Request
{
  "email": "user@example.com",
  "password": "secret"
}
// Response 200
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": { "id": "uuid", "email": "...", "role": "admin", "tenant_id": "uuid" }
}
```

### POST /api/v1/auth/refresh
```json
// Request
{ "refresh": "eyJ..." }
// Response 200
{ "access": "eyJ..." }
```

---

## Tenants

### GET /api/v1/tenants/ — List tenants (superuser only)
### POST /api/v1/tenants/ — Create tenant
### GET /api/v1/tenants/{id}/ — Get tenant
### PATCH /api/v1/tenants/{id}/ — Update tenant

---

## Knowledge Bases

### GET /api/v1/knowledge-bases/
```json
// Response 200
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "name": "Product Docs",
      "embedding_model": "text-embedding-3-small",
      "chunk_size": 512,
      "doc_count": 42,
      "chunk_count": 1200,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /api/v1/knowledge-bases/
```json
// Request
{
  "name": "Product Docs",
  "description": "Official product documentation",
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 512,
  "chunk_overlap": 64,
  "retrieval_top_k": 5
}
```

### GET /api/v1/knowledge-bases/{id}/
### PATCH /api/v1/knowledge-bases/{id}/
### DELETE /api/v1/knowledge-bases/{id}/

---

## Documents

### GET /api/v1/knowledge-bases/{kb_id}/documents/
Query params: `status`, `source_type`, `search`, `page`, `page_size`

### POST /api/v1/knowledge-bases/{kb_id}/documents/upload/
```
Content-Type: multipart/form-data
file: <binary>
name: "my-document.pdf"  (optional)
```
```json
// Response 201
{
  "id": "uuid",
  "name": "my-document.pdf",
  "status": "pending",
  "source_type": "file",
  "mime_type": "application/pdf",
  "file_size": 102400
}
```

### POST /api/v1/knowledge-bases/{kb_id}/documents/import-url/
```json
// Request
{
  "url": "https://docs.example.com/guide",
  "render_mode": "static",   // static | selenium | playwright
  "name": "Guide Page"       // optional
}
```

### GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/
### DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/

### POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reindex/
Re-trigger parsing + embedding for a document.

### GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks/
Preview chunks for a document.
```json
// Response 200
{
  "count": 24,
  "results": [
    {
      "id": "uuid",
      "chunk_index": 0,
      "text": "This is the first chunk...",
      "page": 1,
      "token_count": 128
    }
  ]
}
```

---

## FAQ

### GET /api/v1/knowledge-bases/{kb_id}/faq/
Query params: `search`, `tags`, `is_active`, `page`

### POST /api/v1/knowledge-bases/{kb_id}/faq/
```json
// Request
{
  "question": "What is the return policy?",
  "answer": "We offer 30-day returns on all products.",
  "tags": ["policy", "returns"]
}
```

### GET /api/v1/knowledge-bases/{kb_id}/faq/{faq_id}/
### PATCH /api/v1/knowledge-bases/{kb_id}/faq/{faq_id}/
### DELETE /api/v1/knowledge-bases/{kb_id}/faq/{faq_id}/

### POST /api/v1/knowledge-bases/{kb_id}/faq/bulk-import/
```json
// Request
{
  "items": [
    { "question": "Q1", "answer": "A1" },
    { "question": "Q2", "answer": "A2" }
  ]
}
```

---

## Core RAG APIs

### 1. Retrieval API — Search only

**POST /api/v1/retrieval/search**
```json
// Request
{
  "query": "What is the return policy for damaged items?",
  "knowledge_base_id": "uuid",
  "top_k": 5,
  "filters": {
    "source_type": ["file", "faq"],
    "document_ids": ["uuid1", "uuid2"]  // optional
  },
  "score_threshold": 0.5
}

// Response 200
{
  "query": "What is the return policy...",
  "total": 5,
  "chunks": [
    {
      "id": "uuid",
      "text": "We offer 30-day returns...",
      "score": 0.92,
      "source": {
        "type": "file",
        "name": "return-policy.pdf",
        "document_id": "uuid",
        "page": 3,
        "url": null
      },
      "metadata": {
        "chunk_index": 5,
        "knowledge_base_id": "uuid",
        "embedding_model": "text-embedding-3-small"
      }
    }
  ],
  "latency_ms": 45
}
```

---

### 2. Prompt Builder API — Returns enhanced prompt

**POST /api/v1/rag/prompt**
```json
// Request
{
  "query": "What is the return policy for damaged items?",
  "knowledge_base_id": "uuid",
  "top_k": 5,
  "system_prompt": "You are a helpful assistant."  // optional override
}

// Response 200
{
  "query": "What is the return policy...",
  "context": [
    {
      "text": "We offer 30-day returns...",
      "score": 0.92,
      "source": "return-policy.pdf (page 3)"
    }
  ],
  "prompt": {
    "system": "You are a helpful assistant. Answer using the provided context only.",
    "context_block": "Context:\n[1] We offer 30-day returns...\n[2] ...",
    "user": "What is the return policy for damaged items?",
    "full_prompt": "..."
  },
  "token_estimate": 512
}
```

---

### 3. Answer API — Full RAG pipeline

**POST /api/v1/rag/answer**
```json
// Request
{
  "query": "What is the return policy for damaged items?",
  "knowledge_base_id": "uuid",
  "top_k": 5,
  "llm_model": "claude-sonnet-4-6",  // optional
  "stream": false,
  "system_prompt": "..."  // optional
}

// Response 200 (non-stream)
{
  "query": "What is the return policy...",
  "answer": "For damaged items, you can return them within 30 days...",
  "sources": [
    {
      "text": "We offer 30-day returns...",
      "score": 0.92,
      "source": "return-policy.pdf (page 3)"
    }
  ],
  "usage": {
    "prompt_tokens": 512,
    "completion_tokens": 128,
    "total_tokens": 640
  },
  "latency_ms": 1240
}

// Response 200 (stream=true) — SSE
data: {"type": "chunk", "content": "For damaged"}
data: {"type": "chunk", "content": " items"}
data: {"type": "done", "sources": [...], "usage": {...}}
```

---

## Jobs / Status

### GET /api/v1/jobs/parse/{doc_id}/
### GET /api/v1/jobs/embed/{doc_id}/
```json
// Response 200
{
  "status": "running",
  "progress": 45,
  "total_chunks": 100,
  "done_chunks": 45,
  "started_at": "2024-01-01T00:00:00Z"
}
```

---

## Audit Logs

### GET /api/v1/audit/retrieval/
Query params: `knowledge_base_id`, `start_date`, `end_date`, `page`

### GET /api/v1/audit/queries/
Query params: `knowledge_base_id`, `start_date`, `end_date`, `page`

---

## Error Format

All errors follow:
```json
{
  "error": "validation_error",
  "message": "Human-readable description",
  "details": { "field": ["error detail"] }
}
```

HTTP status codes:
- `400` Bad Request
- `401` Unauthorized
- `403` Forbidden (wrong tenant)
- `404` Not Found
- `429` Rate Limited
- `500` Internal Server Error
