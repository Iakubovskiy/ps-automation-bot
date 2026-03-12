"""Organization domain entity.

An Organization represents a tenant — a company or brand that uses the platform.
Each Organization has its own S3 storage credentials and owns Users, Products, etc.
"""
import uuid

from django.db import models

from core.events import EventBus
from core.events.org_created import OrgCreatedEvent


class Organization(models.Model):
    """A tenant organization on the platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    # S3 / MinIO credentials per organization
    s3_endpoint = models.CharField(max_length=512, blank=True, default="")
    s3_access_key = models.CharField(max_length=255, blank=True, default="")
    s3_secret_key = models.CharField(max_length=255, blank=True, default="")
    s3_bucket_name = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_organization"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self) -> str:
        return self.name

    # ── Rich Model behaviour ─────────────────────────────────────────

    @classmethod
    def create(cls, name: str, **s3_kwargs) -> "Organization":
        """Factory method: create an Organization and publish OrgCreatedEvent."""
        org = cls.objects.create(name=name, **s3_kwargs)
        EventBus.publish(
            OrgCreatedEvent(
                organization_id=str(org.id),
                name=org.name,
            )
        )
        return org

    @property
    def active_integrations(self) -> list[str]:
        """Повертає список типів активних драйверів (наприклад, ['horoshop', 'etsy'])."""
        # Локальний імпорт для уникнення циклічних залежностей між модулями users та distribution
        from modules.distribution.domain.distribution_driver import DistributionDriver, DriverStatus

        return list(
            DistributionDriver.objects.filter(
                organization_id=self.id,
                status=DriverStatus.ACTIVE
            ).values_list("driver_type", flat=True)
        )
