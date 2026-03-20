from django.db import models
from common.models import TenantScopedModel
from tenants.models import Tenant
from knowledge_bases.models import KnowledgeBase


class Document(TenantScopedModel):
    class SourceType(models.TextChoices):
        FILE = "file", "File"
        URL = "url", "URL"
        FAQ = "faq", "FAQ"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARSING = "parsing", "Parsing"
        PARSED = "parsed", "Parsed"
        CHUNKING = "chunking", "Chunking"
        CHUNKED = "chunked", "Chunked"
        EMBEDDING = "embedding", "Embedding"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="documents", to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=500)
    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=1000, blank=True)   # MinIO object key
    source_url = models.CharField(max_length=2000, blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING, db_index=True)
    error_message = models.TextField(blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    chunk_count = models.IntegerField(default=0)
    word_count = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, blank=True)
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class DocumentVersion(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version = models.IntegerField(default=1)
    file_path = models.CharField(max_length=1000, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "document_versions"
        unique_together = [("document", "version")]


class DocumentChunk(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name="chunks")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    text = models.TextField()
    text_length = models.IntegerField()
    token_count = models.IntegerField(null=True, blank=True)
    page = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=500, blank=True)
    embedding_model = models.CharField(max_length=100, blank=True)
    vector_id = models.CharField(max_length=255, blank=True)    # Qdrant point ID
    is_embedded = models.BooleanField(default=False, db_index=True)
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "document_chunks"
        ordering = ["chunk_index"]


class URLSource(TenantScopedModel):
    class RenderMode(models.TextChoices):
        STATIC = "static", "Static"
        SELENIUM = "selenium", "Selenium"
        PLAYWRIGHT = "playwright", "Playwright"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, to_field="id", db_column="tenant_id")
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name="url_sources")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name="url_source")
    url = models.CharField(max_length=2000)
    render_mode = models.CharField(max_length=20, choices=RenderMode.choices, default=RenderMode.STATIC)
    status = models.CharField(max_length=50, default="pending")
    crawl_depth = models.IntegerField(default=0)
    last_crawled_at = models.DateTimeField(null=True, blank=True)
    html_path = models.CharField(max_length=1000, blank=True)
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "url_sources"
