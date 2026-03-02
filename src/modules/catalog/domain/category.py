"""Category domain entity.

A Category defines a product type (e.g. "Hunting Knife", "EDC Knife").
It contains:
  - system_prompt: AI instruction text for Gemini content generation
  - attribute_schema: JSON schema driving the dynamic bot FSM dialog

attribute_schema format:
[
    {
        "key": "steel",
        "label": "Тип сталі",
        "source_type": "STATIC_DB",     # STATIC_DB | MANUAL
        "source_ref": "Steel",          # group_name in StaticReference (for STATIC_DB)
        "data_type": "str",             # str | float | int | list
        "multi_select": false
    },
    {
        "key": "blade_length",
        "label": "Довжина клинка (мм)",
        "source_type": "MANUAL",
        "source_ref": null,
        "data_type": "float",
        "multi_select": false
    }
]
"""
from django.db import models


class Category(models.Model):
    """A product category with an AI prompt and dynamic attribute schema."""

    name = models.CharField(max_length=255, unique=True)
    system_prompt = models.TextField(
        blank=True,
        default="",
        help_text="Instruction text for Gemini AI content generation",
    )
    attribute_schema = models.JSONField(
        default=list,
        help_text="JSON array defining the dynamic bot dialog fields",
    )

    class Meta:
        db_table = "catalog_category"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name

    # ── Rich Model behaviour ─────────────────────────────────────────

    def get_static_db_fields(self) -> list[dict]:
        """Return only attribute_schema fields that reference StaticReference."""
        return [
            field for field in self.attribute_schema
            if field.get("source_type") == "STATIC_DB"
        ]

    def get_manual_fields(self) -> list[dict]:
        """Return only attribute_schema fields requiring manual text input."""
        return [
            field for field in self.attribute_schema
            if field.get("source_type") == "MANUAL"
        ]

    def get_field_by_key(self, key: str) -> dict | None:
        """Look up a single schema field by its key."""
        for field in self.attribute_schema:
            if field.get("key") == key:
                return field
        return None
