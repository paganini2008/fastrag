"""
Qdrant vector store service — backed by LlamaIndex QdrantVectorStore.
"""
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    _qdrant_client = None
    __vector_store = None

    @property
    def client(self):
        if self._qdrant_client is None:
            from qdrant_client import QdrantClient
            kwargs = dict(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, https=False)
            if settings.QDRANT_API_KEY:
                kwargs["api_key"] = settings.QDRANT_API_KEY
            self._qdrant_client = QdrantClient(**kwargs)
        return self._qdrant_client

    @property
    def collection(self) -> str:
        return settings.QDRANT_COLLECTION

    @property
    def _vector_store(self):
        if self.__vector_store is None:
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            self.__vector_store = QdrantVectorStore(client=self.client, collection_name=self.collection)
        return self.__vector_store

    def ensure_collection(self, collection_name: str = None, vector_size: int = None):
        """Create collection and payload indexes if not present."""
        from qdrant_client.models import VectorParams, Distance, HnswConfigDiff, PayloadSchemaType
        collection_name = collection_name or self.collection
        vector_size = vector_size or settings.DEFAULT_EMBEDDING_DIM
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
                on_disk_payload=True,
            )
            for field in ["tenant_id", "knowledge_base_id", "document_id", "source_type"]:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            logger.info(f"Created Qdrant collection: {collection_name}")

    def upsert_chunks(self, points: List[Dict[str, Any]], collection_name: str = None) -> bool:
        """
        Upsert pre-embedded chunk points via LlamaIndex QdrantVectorStore.
        Each point: {"id": str, "vector": List[float], "payload": dict}
        """
        from llama_index.core.schema import TextNode
        from llama_index.vector_stores.qdrant import QdrantVectorStore

        nodes = []
        for p in points:
            node = TextNode(
                id_=p["id"],
                text=p["payload"].get("text", ""),
                metadata=p["payload"],
            )
            node.embedding = p["vector"]
            nodes.append(node)

        if collection_name and collection_name != self.collection:
            store = QdrantVectorStore(client=self.client, collection_name=collection_name)
        else:
            store = self._vector_store
        store.add(nodes)
        return True

    def search(
        self,
        query_vector: List[float],
        tenant_id: str,
        knowledge_base_id: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Search via native qdrant-client for precise payload filtering."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must_conditions = [
            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
            FieldCondition(key="knowledge_base_id", match=MatchValue(value=knowledge_base_id)),
        ]
        if filters and filters.get("source_type"):
            source_types = filters["source_type"]
            if isinstance(source_types, str):
                source_types = [source_types]
            from qdrant_client.models import MatchAny
            must_conditions.append(FieldCondition(key="source_type", match=MatchAny(any=source_types)))

        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold if score_threshold > 0 else None,
            query_filter=Filter(must=must_conditions),
            with_payload=True,
        )
        return [{"id": str(r.id), "score": r.score, "payload": r.payload} for r in response.points]

    def delete_by_document(self, document_id: str, collection_name: str = None):
        """Delete all vectors for a document."""
        from qdrant_client.models import FilterSelector, Filter, FieldCondition, MatchValue
        self.client.delete(
            collection_name=collection_name or self.collection,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
            ),
        )

    def delete_points(self, point_ids: List[str]):
        """Delete specific points by ID."""
        from qdrant_client.models import PointIdsList
        self.client.delete(collection_name=self.collection, points_selector=PointIdsList(points=point_ids))
