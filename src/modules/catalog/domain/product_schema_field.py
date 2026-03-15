"""ProductSchemaField — structured inline model replacing raw JSON attribute_schema.

Each row represents one field in the product schema's data collection schema,
with proper form controls in Django admin (dropdowns, checkboxes, text inputs).
"""
from django.db import models

from core.attribute_schema import SourceType, DataType


class ProductSchemaField(models.Model):
    """A single attribute field definition within a ProductSchema."""

    SOURCE_TYPE_CHOICES = [(s.value, s.value) for s in SourceType]
    DATA_TYPE_CHOICES = [(d.value, d.value) for d in DataType]

    product_schema = models.ForeignKey(
        "catalog.ProductSchema",
        on_delete=models.CASCADE,
        related_name="fields",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in the bot dialog (0 = first)",
    )
    key = models.CharField(
        max_length=128,
        help_text='Technical key, e.g. "blade_name", "steel"',
    )
    label = models.CharField(
        max_length=255,
        help_text='Display label, e.g. "Назва ножа", "Сталь"',
    )
    data_type = models.CharField(
        max_length=16,
        choices=DATA_TYPE_CHOICES,
        default=DataType.STR,
    )
    source_type = models.CharField(
        max_length=16,
        choices=SOURCE_TYPE_CHOICES,
        default=SourceType.MANUAL,
    )
    source_ref_group = models.ForeignKey(
        "catalog.StaticReferenceGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_schema_fields",
        verbose_name="Source group",
        help_text="StaticReferenceGroup to pull options from (for STATIC_DB)",
    )
    multi_select = models.BooleanField(
        default=False,
        help_text="Allow selecting multiple values",
    )
    auto_fill_from_value = models.BooleanField(
        default=False,
        help_text="Auto-fill item characteristics into collected data",
    )
    optional = models.BooleanField(
        default=False,
        help_text="Allow the user to skip this field",
    )

    class Meta:
        db_table = "catalog_productschemafield"
        verbose_name = "Product Schema Field"
        verbose_name_plural = "Product Schema Fields"
        ordering = ["order", "pk"]
        unique_together = [("product_schema", "key")]

    def __str__(self) -> str:
        return f"{self.key} ({self.source_type})"

    def to_schema_dict(self) -> dict:
        """Convert to the attribute_schema JSON format."""
        d = {
            "key": self.key,
            "label": self.label,
            "data_type": self.data_type,
            "source_type": self.source_type,
        }
        if self.source_ref_group:
            d["source_ref"] = self.source_ref_group.name
        if self.multi_select:
            d["multi_select"] = True
        if self.auto_fill_from_value:
            d["auto_fill_from_value"] = True
        if self.optional:
            d["optional"] = True
        return d
