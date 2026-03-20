from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    summary="Register a new user",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string", "minLength": 8},
                "username": {"type": "string", "description": "Optional — auto-generated if omitted"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Optional — supply an external tenant UUID to link accounts across systems"},
            },
            "required": ["email", "password"],
        }
    },
    responses={201: OpenApiResponse(description="User created")},
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Register and login in one step",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string", "minLength": 8},
                "username": {"type": "string", "description": "Optional — auto-generated if omitted"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Optional — link to an existing external tenant"},
            },
            "required": ["email", "password"],
        }
    },
    responses={201: OpenApiResponse(description="User created with access and refresh tokens")},
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_and_login_view(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()

    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    refresh["tenant_id"] = str(user.tenant_id)
    refresh["role"] = user.role
    refresh["email"] = user.email

    return Response({
        "user": UserSerializer(user).data,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Google login — verify id_token and return JWT",
    description="Accepts a Google `id_token` from an external system that already completed Google OAuth. Verifies it, finds or creates the user, and returns RAG JWTs.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "id_token": {"type": "string", "description": "Google OAuth2 id_token"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Optional — link to an existing external tenant"},
            },
            "required": ["id_token"],
        }
    },
    responses={
        200: OpenApiResponse(description="JWT tokens returned"),
        400: OpenApiResponse(description="Invalid or missing id_token"),
        401: OpenApiResponse(description="Google token verification failed"),
    },
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def google_login_view(request):
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
    from django.conf import settings
    from tenants.models import Tenant
    from rest_framework_simplejwt.tokens import RefreshToken

    token = request.data.get("id_token", "").strip()
    if not token:
        return Response({"error": "validation_error", "message": "id_token is required"}, status=400)

    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        return Response({"error": "configuration_error", "message": "Google login is not configured"}, status=500)

    try:
        payload = google_id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    except Exception:
        return Response({"error": "auth_error", "message": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED)

    email = payload.get("email")
    if not email:
        return Response({"error": "auth_error", "message": "Google token missing email"}, status=status.HTTP_401_UNAUTHORIZED)

    external_tenant_id = request.data.get("tenant_id")

    # Find existing user first
    from .models import User
    user = User.objects.filter(email=email).first()

    if not user:
        # Determine tenant
        if external_tenant_id:
            import uuid as _uuid
            tenant, _ = Tenant.objects.get_or_create(
                id=external_tenant_id,
                defaults={"name": str(external_tenant_id), "slug": str(external_tenant_id)},
            )
        else:
            import uuid as _uuid
            tid = _uuid.uuid4()
            tenant = Tenant.objects.create(name=str(tid), slug=str(tid))

        username = payload.get("name") or f"user_{email.split('@')[0]}"
        user = User.objects.create_user(
            email=email,
            username=username,
            tenant_id=tenant.id,
            role=User.Role.OWNER,
            password=None,
        )

    refresh = RefreshToken.for_user(user)
    refresh["tenant_id"] = str(user.tenant_id)
    refresh["role"] = user.role
    refresh["email"] = user.email

    return Response({
        "user": UserSerializer(user).data,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


@extend_schema(
    methods=["GET"],
    summary="Get current user profile",
    responses={200: OpenApiResponse(description="User profile")},
    tags=["Auth"],
)
@extend_schema(
    methods=["PATCH"],
    summary="Update current user profile",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
            },
        }
    },
    responses={200: OpenApiResponse(description="Updated user profile")},
    tags=["Auth"],
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request):
    if request.method == "PATCH":
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)
    return Response(UserSerializer(request.user).data)
