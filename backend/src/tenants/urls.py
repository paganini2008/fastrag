from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantSettingsView

router = DefaultRouter()
router.register(r"", TenantViewSet, basename="tenants")
urlpatterns = [
    path("settings/", TenantSettingsView.as_view(), name="tenant-settings"),
    *router.urls,
]
