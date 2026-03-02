"""DistributionDriver domain entity.

Represents a configured publishing platform (e.g. Horoshop, Etsy).
Stores credentials and references the manifest that defines field mapping.
"""
import uuid

from django.db import models


class DriverStatus(models.TextChoices):
    """Whether a driver is active for publishing."""

    ACTIVE = "ACTIVE", "Active"
    DISABLED = "DISABLED", "Disabled"


class DistributionDriver(models.Model):
    """A configured publishing target platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(
        db_index=True,
        help_text="FK to Organization (denormalized via events)",
    )
    name = models.CharField(
        max_length=128,
        help_text='Human-readable name, e.g. "Horoshop Production"',
    )
    driver_type = models.CharField(
        max_length=64,
        help_text='Driver class identifier, e.g. "horoshop"',
    )
    credentials = models.JSONField(
        default=dict,
        help_text="Platform-specific credentials (URL, email, password, API keys)",
    )
    status = models.CharField(
        max_length=16,
        choices=DriverStatus.choices,
        default=DriverStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "distribution_driver"
        verbose_name = "Distribution Driver"
        verbose_name_plural = "Distribution Drivers"

    def __str__(self) -> str:
        return f"{self.name} ({self.driver_type})"

    @property
    def is_active(self) -> bool:
        return self.status == DriverStatus.ACTIVE
