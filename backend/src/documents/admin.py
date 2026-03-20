from django.contrib import admin
from .models import Document, DocumentChunk, DocumentVersion, URLSource

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "source_type", "status", "chunk_count", "knowledge_base_id", "created_at"]
    list_filter = ["status", "source_type"]
    search_fields = ["name"]
    readonly_fields = ["chunk_count", "page_count", "word_count"]

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "chunk_index", "text_length", "token_count", "is_embedded", "page"]
    list_filter = ["is_embedded"]
    search_fields = ["text"]
    raw_id_fields = ["document"]

@admin.register(URLSource)
class URLSourceAdmin(admin.ModelAdmin):
    list_display = ["url", "render_mode", "status", "last_crawled_at", "created_at"]
    list_filter = ["render_mode", "status"]
