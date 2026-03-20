from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tenant_id"] = str(user.tenant_id)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "username": self.user.username,
            "role": self.user.role,
            "tenant_id": str(self.user.tenant_id),
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "tenant_id", "is_active", "created_at"]
        read_only_fields = ["id", "tenant_id", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(required=False, default="")
    tenant_id = serializers.UUIDField(write_only=True, required=False, default=None)

    class Meta:
        model = User
        fields = ["email", "username", "password", "tenant_id"]

    def create(self, validated_data):
        import uuid as _uuid
        from tenants.models import Tenant

        if not validated_data.get("username"):
            validated_data["username"] = f"user_{_uuid.uuid4().hex[:8]}"

        external_tenant_id = validated_data.pop("tenant_id", None)

        if external_tenant_id:
            tenant, _ = Tenant.objects.get_or_create(
                id=external_tenant_id,
                defaults={"name": str(external_tenant_id), "slug": str(external_tenant_id)},
            )
        else:
            tenant_id = _uuid.uuid4()
            tenant = Tenant.objects.create(name=str(tenant_id), slug=str(tenant_id))

        validated_data["tenant_id"] = tenant.id
        validated_data["role"] = User.Role.OWNER
        return User.objects.create_user(**validated_data)
