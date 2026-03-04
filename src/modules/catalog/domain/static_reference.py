"""StaticReference domain entity.

An item within a StaticReferenceGroup. Each item has a key, display label,
and a value JSON object whose structure matches the group's field_schema.

Example for group "Blade Names":
    key: "yakut"
    label: "Якутський"
    value: {
        "blade_type": "Drop point",
        "hardness": "58-60 HRC",
        "weight": 150,
        "total_length": 265,
        "blade_length": 140,
        "width": 30,
        "spine_thickness": 3.5,
        "sharpening_angle": 25
    }
"""
import uuid

from django.db import models


class StaticReference(models.Model):
    """A named reference item within a group, with structured values."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        "catalog.StaticReferenceGroup",
        on_delete=models.CASCADE,
        related_name="items",
    )
    key = models.CharField(
        max_length=128,
        help_text='Technical identifier, e.g. "yakut", "D2"',
    )
    label = models.CharField(
        max_length=255,
        help_text='Display text for bot buttons, e.g. "Якутський"',
    )
    value = models.JSONField(
        default=dict,
        blank=True,
        help_text="Characteristic values matching the group's field_schema",
    )

    class Meta:
        db_table = "catalog_static_reference"
        verbose_name = "Static Reference"
        verbose_name_plural = "Static References"
        unique_together = [("group", "key")]
        ordering = ["label"]

    def __str__(self) -> str:
        return f"{self.group.name}: {self.label}"
