"""Distribution module — publishes products to marketplaces."""
from django.apps import AppConfig


class DistributionConfig(AppConfig):
    """Django app config for the Distribution bounded context."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.distribution"
    label = "distribution"
    verbose_name = "Distribution"
