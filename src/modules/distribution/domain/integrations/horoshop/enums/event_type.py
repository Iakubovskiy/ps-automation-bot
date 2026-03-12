"""Event type enum for Horoshop."""
from django.db import models


class EventType(models.TextChoices):
    """The lifecycle event that triggers this manifest."""
    CREATE = "CREATE", "Create Product"
    UPDATE = "UPDATE", "Update Product"
    DELETE = "DELETE", "Delete Product"
