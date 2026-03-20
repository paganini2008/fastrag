"""
Tenant context middleware.
Extracts tenant_id from JWT token or API key and attaches it to request.
"""
from django.utils.functional import SimpleLazyObject


def get_tenant_from_request(request):
    """Extract tenant from authenticated user."""
    if not hasattr(request, "_cached_tenant"):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            from tenants.models import Tenant
            try:
                request._cached_tenant = Tenant.objects.get(id=user.tenant_id)
            except Tenant.DoesNotExist:
                request._cached_tenant = None
        else:
            request._cached_tenant = None
    return request._cached_tenant


class TenantMiddleware:
    """Attach tenant to every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = SimpleLazyObject(lambda: get_tenant_from_request(request))
        response = self.get_response(request)
        return response
