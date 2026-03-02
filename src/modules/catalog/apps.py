"""Catalog module — PIM core: Categories, Products, Static References."""
from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Django app config for the Catalog bounded context."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.catalog"
    label = "catalog"
    verbose_name = "Catalog (PIM)"
