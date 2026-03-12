"""Cross-module event: a Product has been enriched with AI content.

Published by: Catalog module (after AI generation).
Consumed by: Distribution (triggers publish pipeline).
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductEnrichedEvent(DomainEvent):
    """Fired when all third-party/AI data has been added to the product."""

    product_id: str = ""
    organization_id: str = ""
