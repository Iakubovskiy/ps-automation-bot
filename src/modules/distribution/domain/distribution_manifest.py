"""DistributionManifest domain entity.

A manifest defines HOW product data maps to a specific platform's fields.
It is a JSON configuration that the driver reads to know what to fill and where.

Example manifest_config:
{
    "field_mapping": {
        "article": "attributes.product_code",
        "title_ua": "ai_content.title_ua",
        "title_en": "ai_content.title_en",
        "price": "attributes.price",
        "description_ua": "ai_content.description_ua",
        "description_en": "ai_content.description_en"
    },
    "spec_mapping": {
        "tipNozha": "attributes.blade_type",
        "nazvaNozha": "attributes.blade_name",
        "pxvi": "attributes.sheath_type"
    },
    "checkbox_mapping": {
        "steel": "attributes.steel",
        "handle_material": "attributes.handle_material"
    },
    "seo_mapping": {
        "seo_title_ua": "ai_content.title_ua",
        "seo_keywords_ua": "ai_content.meta_keywords_ua",
        "seo_description_ua": "ai_content.meta_description_ua"
    },
    "selectors": {
        "admin_frame": "iframe[src*='/adminLegacy/data.php']",
        "article_input": "input[name='modifications[0][article]']",
        "save_button": "a:has-text('Зберегти')"
    }
}
"""
import uuid

from django.db import models


class ManifestStatus(models.TextChoices):
    """Publication status for a specific product on a platform."""

    PENDING = "PENDING", "Pending"
    PUBLISHED = "PUBLISHED", "Published"
    FAILED = "FAILED", "Failed"


class DistributionManifest(models.Model):
    """Per-product publish record with JSON-driven field mapping config."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        "distribution.DistributionDriver",
        on_delete=models.CASCADE,
        related_name="manifests",
    )
    product_id = models.UUIDField(
        db_index=True,
        help_text="FK to Product (denormalized from Catalog via events)",
    )
    manifest_config = models.JSONField(
        default=dict,
        help_text="JSON config defining field mapping, selectors, and spec mapping",
    )
    status = models.CharField(
        max_length=16,
        choices=ManifestStatus.choices,
        default=ManifestStatus.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "distribution_manifest"
        verbose_name = "Distribution Manifest"
        verbose_name_plural = "Distribution Manifests"
        unique_together = [("driver", "product_id")]

    def __str__(self) -> str:
        return f"Manifest {self.product_id} → {self.driver.name} ({self.status})"

    # ── Rich Model behaviour ─────────────────────────────────────────

    def mark_published(self) -> None:
        """Mark as successfully published."""
        from django.utils import timezone

        self.status = ManifestStatus.PUBLISHED
        self.error_message = ""
        self.published_at = timezone.now()
        self.save(update_fields=["status", "error_message", "published_at"])

    def mark_failed(self, error: str) -> None:
        """Mark as failed with an error message."""
        self.status = ManifestStatus.FAILED
        self.error_message = error
        self.save(update_fields=["status", "error_message"])

    def get_mapped_value(self, product_data: dict, path: str):
        """Resolve a dotted path like 'attributes.steel' from product data dict.

        Args:
            product_data: Flat or nested dict with product + AI content.
            path: Dot-separated path, e.g. 'attributes.blade_name'.

        Returns:
            The resolved value, or None if not found.
        """
        parts = path.split(".")
        current = product_data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
