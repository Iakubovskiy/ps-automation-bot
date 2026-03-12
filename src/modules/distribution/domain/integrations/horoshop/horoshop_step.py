"""HoroshopStep domain entity."""
import uuid

from django.db import models
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest
from modules.distribution.domain.integrations.horoshop.enums.action_type import ActionType


class HoroshopStep(models.Model):
    """A single executable Playwright step belonging to a HoroshopManifest."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manifest = models.ForeignKey(
        HoroshopManifest,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Execution order like 1, 2, 3...",
    )
    action = models.CharField(
        max_length=32,
        choices=ActionType.choices,
    )

    selector = models.CharField(max_length=500, blank=True, default="")
    value_source = models.CharField(max_length=255, blank=True, default="", help_text="Example: attributes.price")
    static_value = models.CharField(max_length=500, blank=True, default="", help_text="Hardcoded value")

    url_source = models.CharField(max_length=255, blank=True, default="", help_text="Example: credentials.store_url")
    static_url = models.CharField(max_length=500, blank=True, default="")

    iframe_selector = models.CharField(max_length=500, blank=True, default="")
    timeout_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Used for wait_timeout")
    force_click = models.BooleanField(default=False, help_text="Force click ignoring overlays")

    class Meta:
        db_table = "distribution_horoshop_step"
        verbose_name = "Horoshop Step"
        verbose_name_plural = "Horoshop Steps"
        ordering = ["order"]

    def __str__(self) -> str:
        return f"Step {self.order}: {self.get_action_display()}"
