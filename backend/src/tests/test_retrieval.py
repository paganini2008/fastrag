"""Tests for Retrieval and RAG APIs."""
import pytest
from unittest.mock import MagicMock
from config.container import container


@pytest.mark.django_db
class TestRetrievalAPI:
    def test_search_missing_query(self, auth_client):
        resp = auth_client.post("/api/v1/retrieval/search/", {
            "knowledge_base_id": "00000000-0000-0000-0000-000000000000",
        }, format="json")
        assert resp.status_code == 400

    def test_search_missing_kb(self, auth_client):
        resp = auth_client.post("/api/v1/retrieval/search/", {
            "query": "test query",
        }, format="json")
        assert resp.status_code == 400

    def test_search_success(self, auth_client, knowledge_base):
        mock_result = MagicMock()
        mock_result.query = "test query"
        mock_result.total = 1
        mock_result.latency_ms = 50
        mock_result.chunks = [
            MagicMock(
                id="chunk-1", text="Test chunk text", score=0.95,
                source_type="file", source_name="test.pdf",
                document_id="doc-1", page=1, url=None,
                chunk_index=0, knowledge_base_id=str(knowledge_base.id),
                embedding_model="text-embedding-3-small",
            )
        ]

        mock_svc = MagicMock()
        mock_svc.search.return_value = mock_result
        with container.retrieval_service.override(mock_svc):
            resp = auth_client.post("/api/v1/retrieval/search/", {
                "query": "test query",
                "knowledge_base_id": str(knowledge_base.id),
                "top_k": 5,
            }, format="json")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["score"] == 0.95

    def test_prompt_api(self, auth_client, knowledge_base):
        mock_result = MagicMock()
        mock_result.query = "test"
        mock_result.total = 0
        mock_result.chunks = []
        mock_result.latency_ms = 10

        mock_svc = MagicMock()
        mock_svc.search.return_value = mock_result
        with container.retrieval_service.override(mock_svc):
            resp = auth_client.post("/api/v1/rag/prompt/", {
                "query": "What is this?",
                "knowledge_base_id": str(knowledge_base.id),
            }, format="json")

        assert resp.status_code == 200
        data = resp.json()
        assert "prompt" in data
        assert "context" in data


@pytest.mark.django_db
class TestChunkingService:
    def test_split_basic(self):
        from chunking.llamaindex_chunker import SentenceSplitterChunker
        chunker = SentenceSplitterChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split_text("Hello world. " * 50)
        assert len(chunks) > 1

    def test_split_pages(self):
        from chunking.llamaindex_chunker import SentenceSplitterChunker
        chunker = SentenceSplitterChunker(chunk_size=30, chunk_overlap=5)
        pages = [
            {"page": 1, "text": "Page one content. " * 30},
            {"page": 2, "text": "Page two content. " * 30},
        ]
        chunks = chunker.split_pages(pages)
        assert len(chunks) > 2
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))
