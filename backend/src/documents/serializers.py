from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ["id", "chunk_index", "text", "page", "section", "token_count", "is_embedded"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "name", "source_type", "mime_type", "file_size",
            "source_url", "status", "error_message", "page_count",
            "chunk_count", "word_count", "language",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "error_message", "page_count",
            "chunk_count", "word_count", "created_at", "updated_at",
        ]
