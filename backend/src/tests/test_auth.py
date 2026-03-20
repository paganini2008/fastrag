"""Tests for authentication endpoints."""
import pytest


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_tenant_and_user(self, api_client):
        resp = api_client.post("/api/v1/auth/register/", {
            "email": "new@example.com",
            "username": "newuser",
            "password": "strongpass123",
            "tenant_name": "My Company",
        }, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"

    def test_register_missing_fields(self, api_client):
        resp = api_client.post("/api/v1/auth/register/", {}, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": "test@example.com",
            "password": "testpass123",
        }, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": "test@example.com",
            "password": "wrongpass",
        }, format="json")
        assert resp.status_code == 401

    def test_me_endpoint(self, auth_client):
        resp = auth_client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"
