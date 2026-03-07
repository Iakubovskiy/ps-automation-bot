"""StaticReferenceGroup domain entity.

A group defines a collection of reference items that share the same structure.
For example, "Blade Names" is a group with 16 items, each having:
blade_type, hardness, weight, total_length, blade_length, width,
spine_thickness, sharpening_angle.

The field_schema JSON defines what characteristics each item in the group has.
"""
import uuid

from django.db import models


class StaticReferenceGroup(models.Model):
    """A named group that defines the structure for its reference items.

    field_schema example:
    [
        {"key": "blade_type", "label": "Тип клинка", "data_type": "str"},
        {"key": "hardness",   "label": "Твердість",  "data_type": "str"},
        {"key": "weight",     "label": "Вага (г)",    "data_type": "int"},
        {"key": "blade_length", "label": "Довжина клинка (мм)", "data_type": "int"},
        {"key": "width",      "label": "Ширина (мм)",   "data_type": "float"},
        {"key": "spine_thickness", "label": "Товщина обуха (мм)", "data_type": "float"},
        {"key": "sharpening_angle", "label": "Кут заточки (°)", "data_type": "int"}
    ]
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="static_reference_groups",
    )
    name = models.CharField(
        max_length=128,
        help_text='Group name, e.g. "Blade Names", "Steel Types", "Handle Materials"',
    )
    field_schema = models.JSONField(
        default=list,
        help_text="JSON array defining what fields each item in this group has",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalog_static_reference_group"
        verbose_name = "Static Reference Group"
        verbose_name_plural = "Static Reference Groups"
        unique_together = [("organization", "name")]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_field_keys(self) -> list[str]:
        """Return just the field keys from the schema."""
        return [f["key"] for f in self.field_schema]
