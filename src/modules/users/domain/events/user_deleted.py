"""Internal event: a User was deleted.

This event stays within the Users module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class UserDeletedEvent(DomainEvent):
    """Fired when a User is removed."""

    user_id: str = ""
    organization_id: str = ""
    email: str = ""
