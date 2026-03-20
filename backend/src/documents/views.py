import os
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from config.container import container
from .models import Document, DocumentChunk
from .serializers import DocumentSerializer, DocumentChunkSerializer
from knowledge_bases.models import KnowledgeBase
from ingestion.tasks import ingest_document, ingest_url, run_async
from django.conf import settings
from common.pagination import StandardPagination


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "source_type"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "file_size"]

    def get_queryset(self):
        return Document.objects.filter(
            tenant_id=self.request.user.tenant_id,
            knowledge_base_id=self.kwargs["kb_id"],
        )

    def get_kb(self):
        return KnowledgeBase.objects.get(
            id=self.kwargs["kb_id"],
            tenant_id=self.request.user.tenant_id,
        )

    @action(detail=False, methods=["post"], url_path="upload", parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, kb_id=None):
        """Upload a file document."""
        kb = self.get_kb()
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "validation_error", "message": "file is required"}, status=400)

        # Create DB record first to get the real UUID
        doc = Document.objects.create(
            tenant_id=request.user.tenant_id,
            knowledge_base=kb,
            name=request.data.get("name", file.name),
            source_type=Document.SourceType.FILE,
            mime_type=file.content_type,
            file_size=file.size,
            status=Document.Status.PENDING,
        )

        # Store in MinIO using the real doc UUID
        minio = container.minio_client()
        tenant_id = str(request.user.tenant_id)
        file_ext = os.path.splitext(file.name)[1]
        object_key = f"raw/{tenant_id}/{doc.id}/file{file_ext}"
        minio.put_object(object_key, file, file.size, file.content_type)
        doc.file_path = object_key
        doc.save(update_fields=["file_path"])

        # Trigger async ingestion
        run_async(ingest_document,str(doc.id))

        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="import-url")
    def import_url(self, request, kb_id=None):
        """Import a URL as document."""
        kb = self.get_kb()
        url = request.data.get("url")
        if not url:
            return Response({"error": "validation_error", "message": "url is required"}, status=400)

        from .models import URLSource  # local to avoid circular import
        url_source = URLSource.objects.create(
            tenant_id=request.user.tenant_id,
            knowledge_base=kb,
            url=url,
            render_mode=request.data.get("render_mode", "static"),
        )
        doc = Document.objects.create(
            tenant_id=request.user.tenant_id,
            knowledge_base=kb,
            name=request.data.get("name", url),
            source_type=Document.SourceType.URL,
            source_url=url,
            status=Document.Status.PENDING,
        )
        url_source.document = doc
        url_source.save(update_fields=["document"])

        run_async(ingest_url, str(doc.id), str(url_source.id))

        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="reindex")
    def reindex(self, request, kb_id=None, pk=None):
        """Re-trigger parsing and embedding."""
        doc = self.get_object()
        doc.status = Document.Status.PENDING
        doc.error_message = ""
        doc.save(update_fields=["status", "error_message"])

        run_async(ingest_document,str(doc.id))

        return Response({"message": "Reindex triggered"})

    @action(detail=True, methods=["get"], url_path="content")
    def content(self, request, kb_id=None, pk=None):
        """Return raw parsed text of a document, truncated at CONTENT_TRUNCATE_LIMIT chars."""
        doc = self.get_object()
        limit = settings.CONTENT_TRUNCATE_LIMIT
        texts = [p["text"] for p in (doc.meta or {}).get("parsed_pages", []) if p.get("text")]

        # Total length computed without building the full string
        sep = 2  # len("\n\n")
        total_length = sum(len(t) for t in texts) + max(0, len(texts) - 1) * sep

        # Only join enough pages to reach the limit
        display_parts, acc = [], 0
        for i, t in enumerate(texts):
            acc += len(t) + (sep if i else 0)
            display_parts.append(t)
            if acc >= limit:
                break

        text = "\n\n".join(display_parts)
        truncated = total_length > limit
        return Response({
            "text": text[:limit] if truncated else text,
            "truncated": truncated,
            "total_length": total_length,
        })

    @action(detail=True, methods=["get"], url_path="chunks")
    def chunks(self, request, kb_id=None, pk=None):
        """Preview chunks for a document."""
        doc = self.get_object()
        chunks = DocumentChunk.objects.filter(document=doc).order_by("chunk_index")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(chunks, request)
        return paginator.get_paginated_response(DocumentChunkSerializer(page, many=True).data)
