"""Event bus — dispatches domain events as Celery tasks."""
import re

from core.events.domain_event import DomainEvent


class EventBus:
    """Simple event bus that dispatches domain events via Celery tasks.

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
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
    return f"handle_{snake}"
