from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeBaseViewSet
from documents.urls import get_document_urls
from faq.urls import get_faq_urls

router = DefaultRouter()
router.register(r"", KnowledgeBaseViewSet, basename="knowledge-bases")

urlpatterns = [
    path("", include(router.urls)),
    path("<uuid:kb_id>/documents/", include(get_document_urls())),
    path("<uuid:kb_id>/faq/", include(get_faq_urls())),
]
