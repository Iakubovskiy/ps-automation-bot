"""Billing module — usage limits and quotas (stub)."""
from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Django app config for the Billing bounded context."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.billing"
    label = "billing"
    verbose_name = "Billing"
