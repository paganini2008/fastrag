import uuid
import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create rag schema in the test database."""
    with django_db_blocker.unblock():
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS rag;")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant(db):
    from tenants.models import Tenant
    return Tenant.objects.create(name="Test Tenant", slug=f"test-{uuid.uuid4().hex[:8]}")


@pytest.fixture
def user(db, tenant):
    from accounts.models import User
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
        tenant_id=tenant.id,
        role="owner",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def knowledge_base(db, tenant):
    from knowledge_bases.models import KnowledgeBase
    return KnowledgeBase.objects.create(
        tenant_id=tenant.id,
        tenant=tenant,
        name="Test KB",
    )
