"""Repository for DistributionTask queries."""
from modules.distribution.domain.distribution_task import (
    DistributionTask,
    TaskStatus,
)


class TaskRepository:
    """Query interface for DistributionTask entities."""

    @staticmethod
    def find_by_product(product_id: str) -> list[DistributionTask]:
        """Return all publishing tasks for a product across all drivers."""
        return list(
            DistributionTask.objects.filter(
                product_id=product_id,
            ).select_related("driver")
        )

    @staticmethod
    def find_pending_by_driver(driver_id: str) -> list[DistributionTask]:
        """Return pending publishing tasks for a specific driver."""
        return list(
            DistributionTask.objects.filter(
                driver_id=driver_id,
                status=TaskStatus.PENDING,
            )
        )

    @staticmethod
    def find_or_create(
            driver_id: str,
            product_id: str,
    ) -> DistributionTask:
        """Get existing task or create a new one for this driver+product in PENDING state."""
        task, created = DistributionTask.objects.get_or_create(
            driver_id=driver_id,
            product_id=product_id,
            defaults={
                "status": TaskStatus.PENDING,
            },
        )

        if not created and task.status == TaskStatus.FAILED:
            task.status = TaskStatus.PENDING
            task.error_message = ""
            task.save(update_fields=["status", "error_message"])

        return task
