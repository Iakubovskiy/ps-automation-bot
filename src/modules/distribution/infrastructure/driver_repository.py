"""Repository for DistributionDriver queries."""
from modules.distribution.domain.distribution_driver import DistributionDriver, DriverStatus


class DriverRepository:
    """Query interface for DistributionDriver entities."""

    @staticmethod
    def find_active_by_organization(organization_id: str) -> list[DistributionDriver]:
        """Return all active drivers for an organization."""
        return list(
            DistributionDriver.objects.filter(
                organization_id=organization_id,
                status=DriverStatus.ACTIVE,
            )
        )

    @staticmethod
    def find_by_id(driver_id: str) -> DistributionDriver | None:
        """Look up a driver by UUID."""
        return DistributionDriver.objects.filter(pk=driver_id).first()

    @staticmethod
    def find_by_type(
        organization_id: str,
        driver_type: str,
    ) -> DistributionDriver | None:
        """Find a driver by type within an organization."""
        return DistributionDriver.objects.filter(
            organization_id=organization_id,
            driver_type=driver_type,
            status=DriverStatus.ACTIVE,
        ).first()
