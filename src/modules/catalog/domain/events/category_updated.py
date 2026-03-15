"""Internal event: a ProductSchema was updated.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductSchemaUpdatedEvent(DomainEvent):
    """Fired when an existing ProductSchema is modified."""

    product_schema_id: int = 0
    name: str = ""
