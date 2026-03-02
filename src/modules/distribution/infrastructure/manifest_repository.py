"""Repository for DistributionManifest queries."""
from modules.distribution.domain.distribution_manifest import (
    DistributionManifest,
    ManifestStatus,
)


class ManifestRepository:
    """Query interface for DistributionManifest entities."""

    @staticmethod
    def find_by_product(product_id: str) -> list[DistributionManifest]:
        """Return all manifests for a product across all drivers."""
        return list(
            DistributionManifest.objects.filter(
                product_id=product_id,
            ).select_related("driver")
        )

    @staticmethod
    def find_pending_by_driver(driver_id: str) -> list[DistributionManifest]:
        """Return pending manifests for a specific driver."""
        return list(
            DistributionManifest.objects.filter(
                driver_id=driver_id,
                status=ManifestStatus.PENDING,
            )
        )

    @staticmethod
    def find_or_create(
        driver_id: str,
        product_id: str,
        manifest_config: dict,
    ) -> DistributionManifest:
        """Get existing manifest or create a new one for this driver+product."""
        manifest, _ = DistributionManifest.objects.get_or_create(
            driver_id=driver_id,
            product_id=product_id,
            defaults={
                "manifest_config": manifest_config,
                "status": ManifestStatus.PENDING,
            },
        )
        return manifest
