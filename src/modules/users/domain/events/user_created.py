"""Internal event: a User was created.

This event stays within the Users module.
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class UserCreatedEvent(DomainEvent):
    """Fired when a new User is created within an Organization."""

    user_id: str = ""
    organization_id: str = ""
    email: str = ""
    role_code: str = ""
