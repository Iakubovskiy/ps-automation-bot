"""Facade for routing manifest queries to the correct integration repository."""
import logging

from modules.distribution.domain.distribution_driver import DistributionDriver
from modules.distribution.infrastructure.integrations.horoshop.horoshop_manifest_repository import HoroshopManifestRepository
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest
from modules.distribution.domain.integrations.horoshop.enums.event_type import EventType
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class ManifestFacadeRepository:
    """Routes manifest lookups based on driver type."""

    @staticmethod
    def find_for_driver(driver_config: DistributionDriver, product_schema_id: str, event_type: EventType):
        """Finds the appropriate manifest for any driver type."""

        if driver_config.driver_type == "horoshop":
            try:
                manifest = HoroshopManifestRepository.find_by_product_schema_and_event(
                    driver_id=str(driver_config.id),
                    product_schema_id=product_schema_id,
                    event_type=event_type
                )
                return list(manifest.steps.all())
            except ObjectDoesNotExist:
                logger.warning(
                    "HoroshopManifest not found for driver_id=%s, product_schema_id=%s, event=%s",
                    driver_config.id, product_schema_id, event_type
                )
                return None
        return None
