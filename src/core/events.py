"""Shared Kernel: Domain Event base class and Event Bus."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Attributes:
        event_id: Unique identifier for this event instance.
        occurred_at: UTC timestamp when the event was created.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a plain dict (JSON-safe for Celery)."""
        from dataclasses import asdict

        return asdict(self)


class EventBus:
    """Simple event bus that dispatches domain events via Celery tasks.

    Usage:
        bus = EventBus()
        bus.publish(ProductCreatedEvent(product_id="...", organization_id="..."))

    Each event class name is mapped to a Celery task name by convention:
        ProductCreatedEvent → handle_product_created_event
    """

    @staticmethod
    def publish(event: DomainEvent) -> None:
        """Dispatch a domain event as a Celery task."""
        from framework.celery import app

        task_name = _event_class_to_task_name(event.__class__.__name__)
        app.send_task(task_name, kwargs={"event_data": event.to_dict()})


def _event_class_to_task_name(class_name: str) -> str:
    """Convert e.g. 'ProductCreatedEvent' → 'handle_product_created_event'."""
    import re

    # CamelCase → snake_case
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
    return f"handle_{snake}"
