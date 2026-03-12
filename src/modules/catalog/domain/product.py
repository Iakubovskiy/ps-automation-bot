"""Product domain entity.

A Product is the central PIM entity — it belongs to an Organization and a Category.
Its attributes are stored as a JSON blob, validated against the Category's attribute_schema.
"""
import uuid

from django.db import models

from core.events import EventBus
from core.events.product_created import ProductCreatedEvent


class ProductStatus(models.TextChoices):
    """Lifecycle states of a Product."""

    DRAFT = "DRAFT", "Draft"
    AI_PROCESSING = "AI_PROCESSING", "AI Processing"
    READY = "READY", "Ready"
    ERROR = "ERROR", "Error"


class Product(models.Model):
    """A product managed by the PIM platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(
        db_index=True,
        help_text="FK to Organization (denormalized from Users module via events)",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        related_name="products",
    )
    attributes = models.JSONField(
        default=dict,
        help_text="Collected data — validated against Category.attribute_schema",
    )
    status = models.CharField(
        max_length=16,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        display_name = str(self.id)
        if self.attributes:
            # Use the first non-empty attribute value as display name
            for value in self.attributes.values():
                if isinstance(value, str) and value:
                    display_name = value
                    break
        return f"{display_name} ({self.status})"

    # ── Rich Model behaviour ─────────────────────────────────────────

    @classmethod
    def create(
        cls,
        organization_id: str,
        category: "Category",
        attributes: dict,
    ) -> "Product":
        """Factory: create a Product in DRAFT status and publish ProductCreatedEvent."""
        product = cls.objects.create(
            organization_id=organization_id,
            category=category,
            attributes=attributes,
            status=ProductStatus.DRAFT,
        )
        EventBus.publish(
            ProductCreatedEvent(
                product_id=str(product.id),
                organization_id=str(product.organization_id),
                category_id=product.category_id,
            )
        )
        return product

    def mark_ai_processing(self) -> None:
        """Transition to AI_PROCESSING status."""
        self.status = ProductStatus.AI_PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_ready(self, ai_attributes: dict | None = None) -> None:
        """Transition to READY, optionally merging AI-generated attributes."""
        if ai_attributes:
            self.attributes.update(ai_attributes)
        self.status = ProductStatus.READY
        self.save(update_fields=["status", "attributes", "updated_at"])

    def mark_error(self) -> None:
        """Transition to ERROR status."""
        self.status = ProductStatus.ERROR
        self.save(update_fields=["status", "updated_at"])
