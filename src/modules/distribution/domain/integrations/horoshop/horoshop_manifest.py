"""HoroshopManifest domain entity."""
import uuid

from django.db import models
from modules.distribution.domain.integrations.horoshop.enums.event_type import EventType


class HoroshopManifest(models.Model):
    """Manifest header defining when and where these steps apply."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        "distribution.DistributionDriver",
        on_delete=models.CASCADE,
        related_name="horoshop_manifests",
    )
    product_schema_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier of the ProductSchema this manifest applies to",
    )
    event_type = models.CharField(
        max_length=16,
        choices=EventType.choices,
        default=EventType.CREATE,
        help_text="The product lifecycle event that triggers this script",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "distribution_horoshop_manifest"
        verbose_name = "Horoshop Manifest"
        verbose_name_plural = "Horoshop Manifests"
        unique_together = [["driver", "product_schema_id", "event_type"]]

    def __str__(self) -> str:
        return f"Horoshop {self.event_type} | Schema: {self.product_schema_id}"
