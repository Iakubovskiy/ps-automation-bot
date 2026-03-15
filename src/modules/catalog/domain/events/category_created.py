"""Internal event: a ProductSchema was created.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductSchemaCreatedEvent(DomainEvent):
    """Fired when a new ProductSchema is created."""

    product_schema_id: int = 0
    name: str = ""
