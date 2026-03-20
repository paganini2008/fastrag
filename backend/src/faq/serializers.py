from rest_framework import serializers
from .models import FAQItem


class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ["id", "question", "answer", "tags", "is_active", "is_embedded", "meta", "created_at", "updated_at"]
        read_only_fields = ["id", "is_embedded", "created_at", "updated_at"]
