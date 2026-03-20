from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, register_view, register_and_login_view, google_login_view, me_view

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("register/", register_view, name="auth-register"),
    path("register-and-login/", register_and_login_view, name="auth-register-and-login"),
    path("google/", google_login_view, name="auth-google"),
    path("me/", me_view, name="auth-me"),
]
