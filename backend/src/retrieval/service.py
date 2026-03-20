"""
Retrieval service — full LlamaIndex pipeline (VectorIndexRetriever + MetadataFilters).
"""
import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    id: str
    text: str
    score: float
    source_type: str
    source_name: str
    document_id: str
    page: Optional[int]
    url: Optional[str]
    chunk_index: int
    knowledge_base_id: str
    embedding_model: str


@dataclass
class RetrievalResult:
    query: str
    chunks: List[RetrievedChunk]
    latency_ms: int
    total: int


class RetrievalService:

    def __init__(self, vector_store=None):
        self._vector_store = vector_store

    def search(
        self,
        query: str,
        knowledge_base_id: str,
        tenant_id: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict] = None,
        log_caller: str = "",
    ) -> RetrievalResult:
        from django.conf import settings
        from knowledge_bases.models import KnowledgeBase
        from llama_index.core import VectorStoreIndex, StorageContext
        from llama_index.core.retrievers import VectorIndexRetriever
        from llama_index.core.vector_stores.types import (
            MetadataFilters, MetadataFilter, FilterOperator,
        )
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.vector_stores.qdrant import QdrantVectorStore

        t0 = time.time()

        kb = KnowledgeBase.objects.get(id=knowledge_base_id, tenant_id=tenant_id)

        embed_model = OpenAIEmbedding(model=kb.embedding_model, api_key=settings.OPENAI_API_KEY)
        collection = kb.collection_name or self._vector_store.collection
        qdrant_store = QdrantVectorStore(
            client=self._vector_store.client,
            collection_name=collection,
        )
        index = VectorStoreIndex.from_vector_store(qdrant_store, embed_model=embed_model)

        filter_list = [
            MetadataFilter(key="tenant_id", value=str(tenant_id)),
            MetadataFilter(key="knowledge_base_id", value=str(knowledge_base_id)),
        ]
        if filters and filters.get("source_type"):
            source_types = filters["source_type"]
            if isinstance(source_types, str):
                source_types = [source_types]
            filter_list.append(
                MetadataFilter(key="source_type", value=source_types, operator=FilterOperator.IN)
            )

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=top_k,
            filters=MetadataFilters(filters=filter_list),
        )

        nodes = retriever.retrieve(query)
        latency_ms = int((time.time() - t0) * 1000)

        chunks = []
        for n in nodes:
            if score_threshold > 0 and n.score < score_threshold:
                continue
            meta = n.node.metadata
            chunks.append(RetrievedChunk(
                id=n.node.node_id,
                text=n.node.get_content(),
                score=n.score,
                source_type=meta.get("source_type", ""),
                source_name=meta.get("source_name", ""),
                document_id=meta.get("document_id", ""),
                page=meta.get("page"),
                url=meta.get("url"),
                chunk_index=meta.get("chunk_index", 0),
                knowledge_base_id=meta.get("knowledge_base_id", ""),
                embedding_model=meta.get("embedding_model", ""),
            ))

        try:
            from audit.models import RetrievalLog
            RetrievalLog.objects.create(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                query=query,
                top_k=top_k,
                filters=filters or {},
                result_count=len(chunks),
                latency_ms=latency_ms,
                caller=log_caller,
            )
        except Exception:
            pass

        return RetrievalResult(query=query, chunks=chunks, latency_ms=latency_ms, total=len(chunks))
