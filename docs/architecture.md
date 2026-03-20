# RAG Platform — System Architecture

## 1. System Overview

A production-grade, multi-tenant RAG (Retrieval-Augmented Generation) platform designed as an **Agent Tool** for robot/AI agent systems.

```
                        ┌─────────────────────────────────────────┐
                        │            Agent / Client                │
                        └───────────────────┬─────────────────────┘
                                            │ HTTP / REST
                        ┌───────────────────▼─────────────────────┐
                        │           Django REST API                │
                        │  (DRF + JWT Auth + Tenant Middleware)    │
                        └──┬──────┬──────┬──────┬─────────────────┘
                           │      │      │      │
              ┌────────────▼┐  ┌──▼──┐  │  ┌───▼──────────┐
              │  Ingestion  │  │ FAQ │  │  │  Retrieval   │
              │  Pipeline   │  │ API │  │  │  Engine      │
              └────┬────────┘  └──┬──┘  │  └───┬──────────┘
                   │              │      │      │
         ┌─────────▼──────────────▼──────▼──────▼─────────┐
         │                  Core Services                   │
         │  Parser │ Chunker │ Embedder │ VectorStore       │
         └──────┬──────────────────────────────┬───────────┘
                │                              │
    ┌───────────▼──────┐           ┌───────────▼──────────┐
    │  PostgreSQL       │           │  Qdrant               │
    │  (Business Data)  │           │  (Vector Index)       │
    └───────────────────┘           └──────────────────────┘
                │
    ┌───────────▼──────┐
    │  MinIO            │
    │  (Object Storage) │
    └───────────────────┘
```

## 2. Multi-Tenant Architecture

Each tenant is fully isolated:

- **Data isolation**: All tables include `tenant_id` FK
- **Vector isolation**: Qdrant payload always carries `tenant_id` for filtered search
- **Auth isolation**: JWT tokens carry tenant claim
- **Storage isolation**: MinIO object keys are prefixed with `tenant_id`

```
Tenant A ──┐
Tenant B ──┼──► API Gateway (tenant middleware) ──► Isolated Data Layer
Tenant C ──┘
```

## 3. Data Flow

### Ingestion Flow

```
Upload File / URL
       │
       ▼
  Store raw in MinIO
  (raw/{tenant_id}/{doc_id}/file.*)
       │
       ▼
  Parse Document
  (PDF/DOCX/XLSX/HTML → plain text + metadata)
       │
       ▼
  Chunk Text
  (RecursiveCharacterTextSplitter, 512 tokens, overlap 64)
       │
       ▼
  Generate Embeddings
  (OpenAI text-embedding-3-small, 1536 dim)
       │
       ▼
  Store chunks in PostgreSQL (document_chunks)
       │
       ▼
  Upsert vectors into Qdrant (document_chunks collection)
       │
       ▼
  Update document status → INDEXED
```

### Retrieval Flow

```
Query
  │
  ▼
Embed query (same model)
  │
  ▼
Qdrant vector search
  (filter: tenant_id + knowledge_base_id)
  │
  ▼
Retrieve top-k chunks
  │
  ▼
Return chunks + scores + metadata
```

### RAG Answer Flow

```
Query
  │
  ▼
Retrieval (top-k chunks)
  │
  ▼
Prompt Builder
  (system prompt + context blocks + user query)
  │
  ▼
LLM (Claude / OpenAI)
  │
  ▼
Answer + sources
```

## 4. Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `accounts` | User registration, login, JWT auth |
| `tenants` | Tenant CRUD, tenant-scoped middleware |
| `knowledge_bases` | KB creation, settings, embedding model config |
| `documents` | Document metadata, versioning, status tracking |
| `faq` | FAQ CRUD, vectorization, search |
| `ingestion` | Async job orchestration (Celery tasks) |
| `parsers` | File format parsing (PDF, DOCX, XLSX, HTML, etc.) |
| `chunking` | Text splitting strategies |
| `embeddings` | Embedding model abstraction (OpenAI, local) |
| `vector_store` | Qdrant client abstraction |
| `retrieval` | Hybrid search, reranking |
| `audit` | Query logs, retrieval logs |
| `common` | Shared utils, pagination, exceptions |

## 5. Technology Stack

### Backend
- Python 3.12
- Django 5.x + Django REST Framework
- PostgreSQL 15 (schema: `rag`)
- Qdrant (vector DB)
- MinIO (S3-compatible object storage)
- Celery + Redis (async task queue)
- JWT (djangorestframework-simplejwt)

### Frontend
- React 18 + TypeScript
- Redux Toolkit + RTK Query
- Vite 5
- Ant Design (UI components)
- Axios

### Infrastructure
- Docker + docker-compose
- Nginx (frontend serving + API proxy)

## 6. Security Design

- JWT-based authentication
- Tenant isolation enforced at ORM level (all querysets filtered by tenant_id)
- API key support for Agent-to-Agent calls
- Rate limiting per tenant
- MinIO pre-signed URLs (no direct public access)
