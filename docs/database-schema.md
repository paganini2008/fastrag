# PostgreSQL Database Schema

Schema: `rag`

## Table Overview

```
tenants
  └── users
  └── knowledge_bases
        └── documents
              └── document_versions
              └── document_chunks
        └── faq_items
        └── url_sources
  └── api_keys
  └── parse_jobs
  └── embedding_jobs
  └── retrieval_logs
  └── query_logs
```

---

## Core Tables

### tenants
```sql
CREATE TABLE rag.tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) NOT NULL UNIQUE,
    plan        VARCHAR(50) NOT NULL DEFAULT 'free',  -- free | pro | enterprise
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    settings    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### users
```sql
CREATE TABLE rag.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    username        VARCHAR(150) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner | admin | member
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);
CREATE INDEX idx_users_tenant ON rag.users(tenant_id);
```

### api_keys
```sql
CREATE TABLE rag.api_keys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES rag.users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    key_hash    VARCHAR(255) NOT NULL UNIQUE,
    prefix      VARCHAR(10) NOT NULL,           -- first 8 chars for display
    scopes      JSONB NOT NULL DEFAULT '["read"]',
    expires_at  TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_api_keys_tenant ON rag.api_keys(tenant_id);
```

### knowledge_bases
```sql
CREATE TABLE rag.knowledge_bases (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    embedding_model     VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    vector_size         INTEGER NOT NULL DEFAULT 1536,
    chunk_size          INTEGER NOT NULL DEFAULT 512,
    chunk_overlap       INTEGER NOT NULL DEFAULT 64,
    retrieval_top_k     INTEGER NOT NULL DEFAULT 5,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    doc_count           INTEGER NOT NULL DEFAULT 0,
    chunk_count         INTEGER NOT NULL DEFAULT 0,
    settings            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_kb_tenant ON rag.knowledge_bases(tenant_id);
```

### documents
```sql
CREATE TABLE rag.documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id) ON DELETE CASCADE,
    name                VARCHAR(500) NOT NULL,
    source_type         VARCHAR(50) NOT NULL,   -- file | url | faq
    mime_type           VARCHAR(100),
    file_size           BIGINT,
    file_path           VARCHAR(1000),          -- MinIO object key
    source_url          VARCHAR(2000),
    status              VARCHAR(50) NOT NULL DEFAULT 'pending',
                        -- pending | parsing | parsed | chunking | chunked
                        -- embedding | indexed | failed
    error_message       TEXT,
    page_count          INTEGER,
    chunk_count         INTEGER NOT NULL DEFAULT 0,
    word_count          INTEGER,
    language            VARCHAR(10),
    meta                JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_documents_tenant ON rag.documents(tenant_id);
CREATE INDEX idx_documents_kb ON rag.documents(knowledge_base_id);
CREATE INDEX idx_documents_status ON rag.documents(status);
```

### document_versions
```sql
CREATE TABLE rag.document_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL DEFAULT 1,
    file_path       VARCHAR(1000),
    file_size       BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version)
);
```

### document_chunks
```sql
CREATE TABLE rag.document_chunks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id) ON DELETE CASCADE,
    document_id         UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    chunk_index         INTEGER NOT NULL,
    text                TEXT NOT NULL,
    text_length         INTEGER NOT NULL,
    token_count         INTEGER,
    page                INTEGER,
    section             VARCHAR(500),
    embedding_model     VARCHAR(100),
    vector_id           VARCHAR(255),           -- Qdrant point ID
    is_embedded         BOOLEAN NOT NULL DEFAULT FALSE,
    meta                JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chunks_tenant ON rag.document_chunks(tenant_id);
CREATE INDEX idx_chunks_document ON rag.document_chunks(document_id);
CREATE INDEX idx_chunks_kb ON rag.document_chunks(knowledge_base_id);
```

### faq_items
```sql
CREATE TABLE rag.faq_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id) ON DELETE CASCADE,
    question            TEXT NOT NULL,
    answer              TEXT NOT NULL,
    tags                JSONB NOT NULL DEFAULT '[]',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    vector_id           VARCHAR(255),
    is_embedded         BOOLEAN NOT NULL DEFAULT FALSE,
    meta                JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_faq_tenant ON rag.faq_items(tenant_id);
CREATE INDEX idx_faq_kb ON rag.faq_items(knowledge_base_id);
```

### url_sources
```sql
CREATE TABLE rag.url_sources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id) ON DELETE CASCADE,
    document_id         UUID REFERENCES rag.documents(id),
    url                 VARCHAR(2000) NOT NULL,
    render_mode         VARCHAR(20) NOT NULL DEFAULT 'static',  -- static | selenium | playwright
    status              VARCHAR(50) NOT NULL DEFAULT 'pending',
    crawl_depth         INTEGER NOT NULL DEFAULT 0,
    last_crawled_at     TIMESTAMPTZ,
    html_path           VARCHAR(1000),          -- MinIO object key for HTML
    meta                JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_url_sources_tenant ON rag.url_sources(tenant_id);
```

### parse_jobs
```sql
CREATE TABLE rag.parse_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    celery_task_id  VARCHAR(255),
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
                    -- pending | running | success | failed
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    duration_ms     INTEGER,
    error           TEXT,
    result          JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_parse_jobs_document ON rag.parse_jobs(document_id);
```

### embedding_jobs
```sql
CREATE TABLE rag.embedding_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    celery_task_id  VARCHAR(255),
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_chunks    INTEGER NOT NULL DEFAULT 0,
    done_chunks     INTEGER NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    duration_ms     INTEGER,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_embedding_jobs_document ON rag.embedding_jobs(document_id);
```

### retrieval_logs
```sql
CREATE TABLE rag.retrieval_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id),
    query               TEXT NOT NULL,
    top_k               INTEGER NOT NULL,
    filters             JSONB NOT NULL DEFAULT '{}',
    result_count        INTEGER NOT NULL DEFAULT 0,
    latency_ms          INTEGER,
    caller              VARCHAR(255),           -- agent name / user / api_key
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_retrieval_logs_tenant ON rag.retrieval_logs(tenant_id);
CREATE INDEX idx_retrieval_logs_created ON rag.retrieval_logs(created_at DESC);
```

### query_logs
```sql
CREATE TABLE rag.query_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    knowledge_base_id   UUID NOT NULL REFERENCES rag.knowledge_bases(id),
    query               TEXT NOT NULL,
    answer              TEXT,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    latency_ms          INTEGER,
    llm_model           VARCHAR(100),
    retrieval_log_id    UUID REFERENCES rag.retrieval_logs(id),
    caller              VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_query_logs_tenant ON rag.query_logs(tenant_id);
CREATE INDEX idx_query_logs_created ON rag.query_logs(created_at DESC);
```
