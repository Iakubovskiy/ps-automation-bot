"""RozetkaCategoryMapping — maps ProductSchema to a Rozetka category ID."""
from django.db import models


class RozetkaCategoryMapping(models.Model):
    """Maps a PIM ProductSchema to a Rozetka category for a given driver."""

    feed_config = models.ForeignKey(
        "distribution.RozetkaFeedConfig",
        on_delete=models.CASCADE,
        related_name="category_mappings",
    )
    product_schema = models.ForeignKey(
        "catalog.ProductSchema",
        on_delete=models.CASCADE,
        related_name="rozetka_category_mappings",
    )
    rozetka_category_id = models.PositiveIntegerField(
        help_text="Rozetka's rz_id for this category",
    )
    rozetka_category_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-readable Rozetka category name (for admin convenience)",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default category for this schema (used when product has no per-product override)",
    )

    class Meta:
        db_table = "distribution_rozetka_category_mapping"
        verbose_name = "Rozetka Category Mapping"
        verbose_name_plural = "Rozetka Category Mappings"
        unique_together = [("feed_config", "product_schema", "rozetka_category_id")]

    def __str__(self) -> str:
        return f"{self.product_schema} → {self.rozetka_category_id}"
