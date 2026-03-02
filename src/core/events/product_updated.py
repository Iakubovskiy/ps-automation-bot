"""Cross-module event: a Product was updated.

Published by: Catalog module.
Consumed by: Distribution (triggers re-publish).
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductUpdatedEvent(DomainEvent):
    """Fired when an existing Product is modified."""

    product_id: str = ""
    organization_id: str = ""
