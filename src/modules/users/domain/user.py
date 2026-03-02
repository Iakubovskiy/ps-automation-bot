"""User domain entity.

A User belongs to an Organization and has a Role.
Can optionally be linked to a Telegram account via telegram_id.
"""
import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.db import models


class User(models.Model):
    """A platform user within an Organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="users",
    )
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    role = models.ForeignKey(
        "users.Role",
        on_delete=models.PROTECT,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    # ── Rich Model behaviour ─────────────────────────────────────────

    def set_password(self, raw_password: str) -> None:
        """Hash and store the password."""
        self.password = make_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        """Check a raw password against the stored hash."""
        return check_password(raw_password, self.password)

    def deactivate(self) -> None:
        """Mark the user as inactive."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def has_permission(self, permission_code: str) -> bool:
        """Delegate permission check to the user's Role."""
        return self.role.has_permission(permission_code)
