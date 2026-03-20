from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import RetrievalLog, QueryLog
from .serializers import RetrievalLogSerializer, QueryLogSerializer


class RetrievalLogListView(generics.ListAPIView):
    serializer_class = RetrievalLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["knowledge_base"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return RetrievalLog.objects.filter(tenant_id=self.request.user.tenant_id)


class QueryLogListView(generics.ListAPIView):
    serializer_class = QueryLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["knowledge_base"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return QueryLog.objects.filter(tenant_id=self.request.user.tenant_id)
