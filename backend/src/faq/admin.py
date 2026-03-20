from django.contrib import admin
from .models import FAQItem

@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ["question", "knowledge_base_id", "is_active", "is_embedded", "created_at"]
    list_filter = ["is_active", "is_embedded"]
    search_fields = ["question", "answer"]
