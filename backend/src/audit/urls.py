from django.urls import path
from .views import RetrievalLogListView, QueryLogListView

urlpatterns = [
    path("retrieval/", RetrievalLogListView.as_view(), name="audit-retrieval"),
    path("queries/", QueryLogListView.as_view(), name="audit-queries"),
]
