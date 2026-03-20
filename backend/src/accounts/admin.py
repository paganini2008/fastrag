from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, APIKey

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "tenant_id", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "username"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Info", {"fields": ("username", "tenant_id", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "username", "tenant_id", "password1", "password2", "role")}),
    )

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "prefix", "tenant_id", "is_active", "last_used_at", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "prefix"]
    readonly_fields = ["key_hash", "prefix", "last_used_at"]
