"""Cross-module event: a Product was created.

Published by: Catalog module.
Consumed by: Distribution (triggers publish pipeline).
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductCreatedEvent(DomainEvent):
    """Fired when a new Product is created and ready for processing."""

    product_id: str = ""
    organization_id: str = ""
    category_id: int = 0
