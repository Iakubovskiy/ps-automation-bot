"""Users module — manages Organizations, Roles, and Users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Django app config for the Users bounded context."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.users"
    label = "users"
    verbose_name = "Users & Organizations"
