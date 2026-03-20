from django.db import models
from common.models import TenantScopedModel
from tenants.models import Tenant
from knowledge_bases.models import KnowledgeBase


class RetrievalLog(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.SET_NULL, null=True)
    query = models.TextField()
    top_k = models.IntegerField()
    filters = models.JSONField(default=dict)
    result_count = models.IntegerField(default=0)
    latency_ms = models.IntegerField(null=True, blank=True)
    caller = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "retrieval_logs"
        ordering = ["-created_at"]


class QueryLog(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.SET_NULL, null=True)
    query = models.TextField()
    answer = models.TextField(blank=True)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    llm_model = models.CharField(max_length=100, blank=True)
    retrieval_log = models.ForeignKey(RetrievalLog, on_delete=models.SET_NULL, null=True, blank=True)
    caller = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "query_logs"
        ordering = ["-created_at"]
