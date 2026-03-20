"""
Central API router for v1 endpoints.
"""
from django.urls import path, include

urlpatterns = [
    # Auth
    path("auth/", include("accounts.urls")),

    # Tenants
    path("tenants/", include("tenants.urls")),

    # Knowledge Bases + nested resources
    path("knowledge-bases/", include("knowledge_bases.urls")),

    # FAQ (also nested under knowledge-bases, standalone here for convenience)
    # Retrieval
    path("retrieval/", include("retrieval.urls")),

    # RAG (prompt builder + answer)
    path("rag/", include("retrieval.rag_urls")),

    # Audit logs
    path("audit/", include("audit.urls")),
]
