from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FAQItem
from .serializers import FAQItemSerializer
from knowledge_bases.models import KnowledgeBase


class FAQViewSet(viewsets.ModelViewSet):
    serializer_class = FAQItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["question", "answer"]

    def get_queryset(self):
        return FAQItem.objects.filter(
            tenant_id=self.request.user.tenant_id,
            knowledge_base_id=self.kwargs["kb_id"],
        )

    def perform_create(self, serializer):
        kb = KnowledgeBase.objects.get(
            id=self.kwargs["kb_id"],
            tenant_id=self.request.user.tenant_id,
        )
        instance = serializer.save(
            tenant_id=self.request.user.tenant_id,
            knowledge_base=kb,
        )
        from ingestion.tasks import embed_faq_item, run_async
        run_async(embed_faq_item, str(instance.id))

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request, kb_id=None):
        kb = KnowledgeBase.objects.get(id=kb_id, tenant_id=request.user.tenant_id)
        items_data = request.data.get("items", [])
        created = []
        for item_data in items_data:
            s = FAQItemSerializer(data=item_data)
            if s.is_valid():
                instance = s.save(tenant_id=request.user.tenant_id, knowledge_base=kb)
                created.append(instance)
        from ingestion.tasks import embed_faq_item, run_async
        for item in created:
            run_async(embed_faq_item, str(item.id))
        return Response({"created": len(created)}, status=status.HTTP_201_CREATED)
