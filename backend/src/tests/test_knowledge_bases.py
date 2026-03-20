"""Tests for Knowledge Base API."""
import pytest


@pytest.mark.django_db
class TestKnowledgeBaseAPI:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/v1/knowledge-bases/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_create(self, auth_client):
        resp = auth_client.post("/api/v1/knowledge-bases/", {
            "name": "My KB",
            "description": "Test KB",
            "chunk_size": 512,
            "chunk_overlap": 64,
            "retrieval_top_k": 5,
        }, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My KB"
        assert data["doc_count"] == 0

    def test_list_after_create(self, auth_client, knowledge_base):
        resp = auth_client.get("/api/v1/knowledge-bases/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    def test_get(self, auth_client, knowledge_base):
        resp = auth_client.get(f"/api/v1/knowledge-bases/{knowledge_base.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test KB"

    def test_update(self, auth_client, knowledge_base):
        resp = auth_client.patch(f"/api/v1/knowledge-bases/{knowledge_base.id}/", {
            "name": "Updated KB",
        }, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated KB"

    def test_delete(self, auth_client, knowledge_base):
        resp = auth_client.delete(f"/api/v1/knowledge-bases/{knowledge_base.id}/")
        assert resp.status_code == 204

    def test_tenant_isolation(self, api_client, knowledge_base):
        """Another tenant cannot see this KB."""
        import uuid
        from tenants.models import Tenant
        from accounts.models import User
        other_tenant = Tenant.objects.create(name="Other", slug=f"other-{uuid.uuid4().hex[:6]}")
        other_user = User.objects.create_user(
            email="other@example.com", username="other",
            password="pass", tenant_id=other_tenant.id
        )
        api_client.force_authenticate(user=other_user)
        resp = api_client.get("/api/v1/knowledge-bases/")
        assert resp.json()["count"] == 0
