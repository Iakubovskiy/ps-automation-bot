"""Internal event: a Category was deleted.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class CategoryDeletedEvent(DomainEvent):
    """Fired when a Category is removed."""

    category_id: int = 0
    name: str = ""
