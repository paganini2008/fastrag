# Qdrant Collection Design

## Collection: `document_chunks`

Single collection, multi-tenant via payload filtering.

### Configuration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance,
    PayloadSchemaType, HnswConfigDiff
)

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="document_chunks",
    vectors_config=VectorParams(
        size=1536,          # text-embedding-3-small dimension
        distance=Distance.COSINE,
    ),
    hnsw_config=HnswConfigDiff(
        m=16,               # number of edges per node
        ef_construct=100,   # index-time candidate list size
    ),
    on_disk_payload=True,   # store payload on disk for large datasets
)
```

### Payload Schema

Every point in Qdrant contains:

```json
{
  "tenant_id":          "uuid-string",
  "knowledge_base_id":  "uuid-string",
  "document_id":        "uuid-string",
  "chunk_id":           "uuid-string",      // PostgreSQL PK
  "chunk_index":        0,
  "text":               "chunk content...",
  "source_type":        "file",             // file | url | faq
  "source_name":        "document.pdf",
  "page":               1,
  "url":                null,
  "mime_type":          "application/pdf",
  "embedding_model":    "text-embedding-3-small",
  "created_at":         "2024-01-01T00:00:00Z"
}
```

### Payload Indexes (for fast filtering)

```python
# Create payload indexes for filtered search
client.create_payload_index(
    collection_name="document_chunks",
    field_name="tenant_id",
    field_schema=PayloadSchemaType.KEYWORD,
)
client.create_payload_index(
    collection_name="document_chunks",
    field_name="knowledge_base_id",
    field_schema=PayloadSchemaType.KEYWORD,
)
client.create_payload_index(
    collection_name="document_chunks",
    field_name="document_id",
    field_schema=PayloadSchemaType.KEYWORD,
)
client.create_payload_index(
    collection_name="document_chunks",
    field_name="source_type",
    field_schema=PayloadSchemaType.KEYWORD,
)
```

### Search Example

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="document_chunks",
    query_vector=query_embedding,           # list[float], len=1536
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value="tenant-uuid"),
            ),
            FieldCondition(
                key="knowledge_base_id",
                match=MatchValue(value="kb-uuid"),
            ),
        ]
    ),
    with_payload=True,
    score_threshold=0.5,
)
```

### Point ID Strategy

Use UUID v4 as point ID (Qdrant supports UUID point IDs natively).
The UUID matches the `document_chunks.id` in PostgreSQL for easy cross-reference.

```python
import uuid

point_id = str(uuid.uuid4())  # same as document_chunks.id
```

### Collections Summary

| Collection | Vector Size | Distance | Purpose |
|------------|-------------|----------|---------|
| `document_chunks` | 1536 | Cosine | All chunks (docs + FAQ) |

Note: FAQ items are stored in the same `document_chunks` collection with `source_type = "faq"`.
