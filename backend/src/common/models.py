"""
Shared abstract base models.
"""
import uuid
from django.db import models


class UUIDModel(models.Model):
    """Base model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantScopedModel(UUIDModel):
    """Base model with UUID PK + tenant_id + timestamps."""
    tenant_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
