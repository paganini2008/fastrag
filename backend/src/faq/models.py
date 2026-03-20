from django.db import models
from common.models import TenantScopedModel
from tenants.models import Tenant
from knowledge_bases.models import KnowledgeBase


class FAQItem(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name="faq_items")
    question = models.TextField()
    answer = models.TextField()
    tags = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    vector_id = models.CharField(max_length=255, blank=True)
    is_embedded = models.BooleanField(default=False)
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "faq_items"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]
