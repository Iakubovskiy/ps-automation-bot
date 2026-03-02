"""StaticReference domain entity.

Stores characteristic options (e.g. steel types, handle materials) per Organization.
Replaces Google Sheets lookups with database-backed references.
Used by the bot to build inline keyboards for STATIC_DB attribute fields.
"""
import uuid

from django.db import models


class StaticReference(models.Model):
    """A named characteristic value within a reference group.

    Examples:
        group_name="Steel", key="D2", label="Сталь D2", value={"hardness_range": "58-60"}
        group_name="Handle", key="micarta", label="Мікарта", value={}
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(
        db_index=True,
        help_text="FK to Organization (denormalized from Users module via events)",
    )
    group_name = models.CharField(
        max_length=128,
        db_index=True,
        help_text='Reference group, e.g. "Steel", "Handle", "SheathColor"',
    )
    key = models.CharField(
        max_length=128,
        help_text='Technical identifier, e.g. "D2", "micarta"',
    )
    value = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed data about this reference option",
    )
    label = models.CharField(
        max_length=255,
        help_text='Display text for bot buttons, e.g. "Сталь D2"',
    )

    class Meta:
        db_table = "catalog_static_reference"
        verbose_name = "Static Reference"
        verbose_name_plural = "Static References"
        unique_together = [("organization_id", "group_name", "key")]
        ordering = ["group_name", "label"]

    def __str__(self) -> str:
        return f"{self.group_name}: {self.label}"
