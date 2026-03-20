from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FAQViewSet


def get_faq_urls():
    router = DefaultRouter()
    router.register(r"", FAQViewSet, basename="faq")
    return router.urls
