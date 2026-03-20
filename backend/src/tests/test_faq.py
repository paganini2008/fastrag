"""Tests for FAQ API."""
import pytest


@pytest.mark.django_db
class TestFAQAPI:
    def test_create_faq(self, auth_client, knowledge_base, mocker):
        mocker.patch("ingestion.tasks.run_async")
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/faq/",
            {"question": "What is RAG?", "answer": "Retrieval-Augmented Generation."},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["question"] == "What is RAG?"
        assert data["is_embedded"] is False  # not yet embedded

    def test_list_faq(self, auth_client, knowledge_base):
        resp = auth_client.get(f"/api/v1/knowledge-bases/{knowledge_base.id}/faq/")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_delete_faq(self, auth_client, knowledge_base, mocker):
        mocker.patch("ingestion.tasks.run_async")
        create_resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/faq/",
            {"question": "Q", "answer": "A"},
            format="json",
        )
        faq_id = create_resp.json()["id"]
        del_resp = auth_client.delete(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/faq/{faq_id}/"
        )
        assert del_resp.status_code == 204

    def test_bulk_import(self, auth_client, knowledge_base, mocker):
        mocker.patch("ingestion.tasks.run_async")
        resp = auth_client.post(
            f"/api/v1/knowledge-bases/{knowledge_base.id}/faq/bulk-import/",
            {"items": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"},
            ]},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["created"] == 3
