"""DistributionTask domain entity.

Tracks the STATUS of publishing a specific product to a platform.
"""
import uuid

from django.db import models


class TaskStatus(models.TextChoices):
    """Publication status for a specific product on a platform."""

    PENDING = "PENDING", "Pending"
    PUBLISHED = "PUBLISHED", "Published"
    FAILED = "FAILED", "Failed"


class DistributionTask(models.Model):
    """Per-product publish record tracking the status of the operation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        "distribution.DistributionDriver",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    product_id = models.UUIDField(
        db_index=True,
        help_text="FK to Product (denormalized from Catalog via events)",
    )
    status = models.CharField(
        max_length=16,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "distribution_task"
        verbose_name = "Distribution Task"
        verbose_name_plural = "Distribution Tasks"
        unique_together = [("driver", "product_id")]

    def __str__(self) -> str:
        return f"Task {self.product_id} → {self.driver.name} ({self.status})"


    def mark_published(self) -> None:
        """Mark as successfully published."""
        from django.utils import timezone

        self.status = TaskStatus.PUBLISHED
        self.error_message = ""
        self.published_at = timezone.now()
        self.save(update_fields=["status", "error_message", "published_at"])

    def mark_failed(self, error: str) -> None:
        """Mark as failed with an error message."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.save(update_fields=["status", "error_message"])