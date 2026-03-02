"""Role domain entity.

A Role defines a set of permissions within an Organization.
Standard roles: OWNER, ADMIN, MANAGER.
"""
import uuid

from django.db import models


class Role(models.Model):
    """A named role with a set of permission codes."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"

    CODE_CHOICES = [
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MANAGER, "Manager"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, choices=CODE_CHOICES)
    permissions = models.JSONField(
        default=list,
        help_text="List of permission code strings, e.g. ['product.create', 'product.publish']",
    )

    class Meta:
        db_table = "users_role"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.code

    # ── Rich Model behaviour ─────────────────────────────────────────

    def has_permission(self, permission_code: str) -> bool:
        """Check whether this role grants the given permission."""
        return permission_code in self.permissions
