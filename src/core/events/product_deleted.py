"""Cross-module event: a Product was deleted.

Published by: Catalog module.
Consumed by: Distribution (triggers un-publish).
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductDeletedEvent(DomainEvent):
    """Fired when a Product is removed."""

    product_id: str = ""
    organization_id: str = ""
