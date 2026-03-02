"""Cross-module event: a new Organization was created.

Published by: Users module.
Consumed by: Catalog (to duplicate organization_id reference).
"""
from dataclasses import dataclass

from core.events import DomainEvent


@dataclass(frozen=True)
class OrgCreatedEvent(DomainEvent):
    """Fired when a new Organization is created."""

    organization_id: str = ""
    name: str = ""
