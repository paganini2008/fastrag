from django.contrib import admin
from .models import RetrievalLog, QueryLog

@admin.register(RetrievalLog)
class RetrievalLogAdmin(admin.ModelAdmin):
    list_display = ["query", "tenant_id", "result_count", "latency_ms", "caller", "created_at"]
    list_filter = ["knowledge_base"]
    search_fields = ["query", "caller"]
    readonly_fields = ["tenant_id", "query", "top_k", "filters", "result_count", "latency_ms"]

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ["query", "tenant_id", "llm_model", "latency_ms", "caller", "created_at"]
    list_filter = ["llm_model"]
    search_fields = ["query", "answer"]
    readonly_fields = ["tenant_id", "query", "answer", "prompt_tokens", "completion_tokens", "latency_ms"]
