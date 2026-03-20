from django.db import models
from common.models import TenantScopedModel
from tenants.models import Tenant


class KnowledgeBase(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="knowledge_bases", to_field="id", db_column="tenant_id")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    embedding_model = models.CharField(max_length=100, default="text-embedding-3-small")
    vector_size = models.IntegerField(default=1536)
    chunk_size = models.IntegerField(default=512)
    chunk_overlap = models.IntegerField(default=64)
    retrieval_top_k = models.IntegerField(default=5)
    kb_type = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)
    doc_count = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    settings = models.JSONField(default=dict)
    # Per-KB Qdrant collection (blank = use shared QDRANT_COLLECTION)
    collection_name = models.CharField(max_length=200, blank=True, default="")
    # Rebuild tracking
    rebuild_status = models.CharField(max_length=20, default="idle")  # idle/running/done/failed
    rebuild_progress = models.IntegerField(default=0)  # 0-100

    class Meta:
        db_table = "knowledge_bases"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
