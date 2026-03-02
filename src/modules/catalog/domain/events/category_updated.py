"""Internal event: a Category was updated.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class CategoryUpdatedEvent(DomainEvent):
    """Fired when an existing Category is modified."""

    category_id: int = 0
    name: str = ""
