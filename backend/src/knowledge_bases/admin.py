from django.contrib import admin
from .models import KnowledgeBase

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant_id", "embedding_model", "doc_count", "chunk_count", "is_active", "created_at"]
    list_filter = ["is_active", "embedding_model"]
    search_fields = ["name"]
    readonly_fields = ["doc_count", "chunk_count"]
