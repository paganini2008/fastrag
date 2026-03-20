from rest_framework import serializers
from .models import KnowledgeBase


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            "id", "name", "description", "kb_type", "embedding_model",
            "vector_size", "chunk_size", "chunk_overlap",
            "retrieval_top_k", "is_active", "doc_count", "chunk_count",
            "settings", "collection_name", "rebuild_status", "rebuild_progress",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "doc_count", "chunk_count", "collection_name",
            "rebuild_status", "rebuild_progress", "created_at", "updated_at",
        ]
