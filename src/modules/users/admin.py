"""Django Admin registration for Users module models."""
from django.contrib import admin
from django.contrib.auth.models import User as AuthUser, Group as AuthGroup

from modules.users.domain.organization import Organization

# Hide Django's built-in User and Group — we use our own User model
admin.site.unregister(AuthUser)
admin.site.unregister(AuthGroup)
from modules.users.domain.role import Role
from modules.users.domain.user import User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "created_at")
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "id")
    list_filter = ("code",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "role", "is_active", "telegram_id", "created_at")
    list_filter = ("is_active", "role__code")
    search_fields = ("email",)
