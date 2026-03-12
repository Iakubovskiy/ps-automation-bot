"""Repository for HoroshopManifest queries."""
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest
from modules.distribution.domain.integrations.horoshop.enums.event_type import EventType


class HoroshopManifestRepository:
    """Query interface for Horoshop Manifest entities."""

    @staticmethod
    def find_by_category_and_event(
            driver_id: str,
            category_id: str,
            event_type: EventType = EventType.CREATE
    ) -> HoroshopManifest:
        """Find a specific manifest and eagerly load its ordered steps.

        Args:
            driver_id: ID of the DistributionDriver (the connection).
            category_id: Category ID from the Catalog.
            event_type: The trigger event (e.g., CREATE, UPDATE).

        Raises:
            HoroshopManifest.DoesNotExist: If no matching manifest is found.
        """
        return HoroshopManifest.objects.prefetch_related("steps").get(
            driver_id=driver_id,
            category_id=category_id,
            event_type=event_type,
        )
