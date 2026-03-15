"""Internal event: a ProductSchema was deleted.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class ProductSchemaDeletedEvent(DomainEvent):
    """Fired when a ProductSchema is removed."""

    product_schema_id: int = 0
    name: str = ""
