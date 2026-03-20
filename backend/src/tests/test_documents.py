"""Tests for Document API."""
import io
import pytest
from unittest.mock import MagicMock
from config.container import container


@pytest.fixture
def mock_minio():
    """Mock MinIO client so tests don't need a real MinIO instance."""
    mock = MagicMock()
    with container.minio_client.override(mock):
        yield mock


@pytest.fixture
def mock_ingest(mocker):
    """Prevent background ingestion from running during tests."""
    return mocker.patch("documents.views.run_async")


@pytest.mark.django_db
class TestDocumentUpload:
    def test_upload_no_file(self, auth_client, knowledge_base):
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/upload/",
            {},
            format="multipart",
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "validation_error"

    def test_upload_success(self, auth_client, knowledge_base, mock_minio, mock_ingest):
        file_content = b"This is a test document with some content."
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/upload/",
            {"file": io.BytesIO(file_content)},
            format="multipart",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["source_type"] == "file"
        # MinIO put_object was called
        mock_minio.put_object.assert_called_once()
        # Ingestion was submitted for background execution
        mock_ingest.assert_called_once()

    def test_list_documents(self, auth_client, knowledge_base):
        resp = auth_client.get(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/"
        )
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_import_url(self, auth_client, knowledge_base, mocker):
        mocker.patch("documents.views.run_async")
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/import-url/",
            {"url": "https://example.com/page", "render_mode": "static"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "url"
        assert data["source_url"] == "https://example.com/page"


@pytest.mark.django_db
class TestDocumentChunking:
    def test_chunks_empty_before_indexing(self, auth_client, knowledge_base, mock_minio, mock_ingest):
        # Upload a doc
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/upload/",
            {"file": io.BytesIO(b"test content")},
            format="multipart",
        )
        doc_id = resp.json()["id"]

        # Check chunks (should be empty)
        resp = auth_client.get(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/documents/{doc_id}/chunks/"
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
