from django.urls import path
from .views import prompt_view, answer_view, public_prompt_view

urlpatterns = [
    path("prompt/", prompt_view, name="rag-prompt"),
    path("answer/", answer_view, name="rag-answer"),
    path("public/prompt/", public_prompt_view, name="rag-public-prompt"),
]
