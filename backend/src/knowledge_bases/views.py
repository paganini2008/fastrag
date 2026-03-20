from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from embeddings.constants import MODEL_DIMENSIONS
from .models import KnowledgeBase
from .serializers import KnowledgeBaseSerializer


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "doc_count"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return KnowledgeBase.objects.none()
        return KnowledgeBase.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def rebuild(self, request, pk=None):
        kb = self.get_object()
        new_model = request.data.get("embedding_model", kb.embedding_model)

        if new_model not in MODEL_DIMENSIONS:
            return Response(
                {"detail": f"Unknown embedding model: {new_model}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if kb.rebuild_status == "running":
            return Response(
                {"detail": "Rebuild already in progress"},
                status=status.HTTP_409_CONFLICT,
            )

        KnowledgeBase.objects.filter(id=kb.id).update(
            rebuild_status="running", rebuild_progress=0
        )

        from ingestion.tasks import run_async, rebuild_knowledge_base
        run_async(rebuild_knowledge_base, str(kb.id), new_model)

        kb.refresh_from_db()
        return Response(KnowledgeBaseSerializer(kb).data)
