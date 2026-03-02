"""Internal event: a User was updated.

This event stays within the Users module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class UserUpdatedEvent(DomainEvent):
    """Fired when an existing User is modified."""

    user_id: str = ""
    organization_id: str = ""
