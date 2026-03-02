"""Celery application for the PIM platform."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "framework.settings")

app = Celery("pim_hub")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in each module's application layer.
app.autodiscover_tasks([
    "modules.users",
    "modules.catalog",
    "modules.distribution",
])
