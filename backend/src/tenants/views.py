from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Tenant
from .serializers import TenantSerializer

_SETTING_DEFAULTS = {
    "embedding_model": settings.DEFAULT_EMBEDDING_MODEL,
    "llm_model": settings.DEFAULT_LLM_MODEL,
}


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=user.tenant_id)


class TenantSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenant = request.tenant
        return Response({**_SETTING_DEFAULTS, **(tenant.settings or {})})

    def patch(self, request):
        tenant = request.tenant
        incoming = {k: v for k, v in request.data.items() if k in _SETTING_DEFAULTS}
        tenant.settings = {**(tenant.settings or {}), **incoming}
        tenant.save(update_fields=["settings"])
        return Response({**_SETTING_DEFAULTS, **tenant.settings})
