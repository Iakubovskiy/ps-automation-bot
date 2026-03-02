"""Internal event: a Category was created.

This event stays within the Catalog module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class CategoryCreatedEvent(DomainEvent):
    """Fired when a new Category is created."""

    category_id: int = 0
    name: str = ""
