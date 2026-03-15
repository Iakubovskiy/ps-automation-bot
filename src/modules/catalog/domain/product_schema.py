"""ProductSchema domain entity.

A ProductSchema defines a product data collection structure (fields, AI prompt, attribute schema).
It contains:
  - system_prompt: AI instruction text for Gemini content generation
  - attribute_schema: JSON schema driving the dynamic bot FSM dialog

attribute_schema format:
[
    {
        "key": "steel",
        "label": "Тип сталі",
        "source_type": "STATIC_DB",     # STATIC_DB | MANUAL | AI
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


class ProductSchema(models.Model):
    """A product schema with an AI prompt and dynamic attribute schema."""

    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="product_schemas",
    )
    name = models.CharField(max_length=255)
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
        db_table = "catalog_productschema"
        verbose_name = "Product Schema"
        verbose_name_plural = "Product Schemas"
        unique_together = [("organization", "name")]

    def __str__(self) -> str:
        return self.name

    # ── Rich Model behaviour ─────────────────────────────────────────

    def get_attribute_schema(self) -> list[dict]:
        """Build attribute_schema from related ProductSchemaField records.

        Falls back to the JSON field if no inline attributes exist.
        """
        attrs = list(self.fields.all().order_by("order", "pk"))
        if attrs:
            return [a.to_schema_dict() for a in attrs]
        return self.attribute_schema or []

    async def aget_attribute_schema(self) -> list[dict]:
        """Async version of get_attribute_schema with pre-fetched relations."""
        attrs = [
            a async for a in self.fields.select_related("source_ref_group")
            .all()
            .order_by("order", "pk")
        ]

        if attrs:
            return [a.to_schema_dict() for a in attrs]

        return self.attribute_schema or []

    def get_static_db_fields(self) -> list[dict]:
        """Return only fields that reference StaticReference."""
        return [
            f for f in self.get_attribute_schema()
            if f.get("source_type") == "STATIC_DB"
        ]

    def get_manual_fields(self) -> list[dict]:
        """Return only fields requiring manual text input."""
        return [
            f for f in self.get_attribute_schema()
            if f.get("source_type") == "MANUAL"
        ]

    def get_field_by_key(self, key: str) -> dict | None:
        """Look up a single schema field by its key."""
        for field in self.get_attribute_schema():
            if field.get("key") == key:
                return field
        return None
