from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet


def get_document_urls():
    router = DefaultRouter()
    router.register(r"", DocumentViewSet, basename="documents")
    return router.urls
