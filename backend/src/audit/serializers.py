from rest_framework import serializers
from .models import RetrievalLog, QueryLog


class RetrievalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetrievalLog
        fields = ["id", "query", "top_k", "result_count", "latency_ms", "caller", "created_at"]


class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = ["id", "query", "answer", "prompt_tokens", "completion_tokens", "latency_ms", "llm_model", "caller", "created_at"]
