"""
API Key authentication for Agent-to-Agent calls.
"""
import hashlib
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    """Authenticate using X-API-Key header."""

    keyword = "X-API-Key"

    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY") or request.headers.get("X-API-Key")
        if not api_key:
            return None

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        from accounts.models import APIKey
        from django.utils import timezone

        try:
            key_obj = APIKey.objects.select_related("user").get(
                key_hash=key_hash,
                is_active=True,
            )
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        if key_obj.expires_at and key_obj.expires_at < timezone.now():
            raise AuthenticationFailed("API key expired")

        # Update last used
        APIKey.objects.filter(id=key_obj.id).update(last_used_at=timezone.now())

        return (key_obj.user, key_obj)

    def authenticate_header(self, request):
        return self.keyword
