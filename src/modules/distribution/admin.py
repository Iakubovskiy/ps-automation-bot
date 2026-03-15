"""Django Admin registration for Distribution module models."""
from django.contrib import admin
from django import forms

from modules.distribution.domain.distribution_driver import DistributionDriver
from modules.distribution.domain.distribution_task import DistributionTask
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest
from modules.distribution.domain.integrations.horoshop.horoshop_step import HoroshopStep
from modules.distribution.admin_forms import DistributionDriverForm, HoroshopManifestForm

import modules.distribution.admin_rozetka  # noqa: F401


class HoroshopStepInline(admin.TabularInline):
    model = HoroshopStep
    extra = 1
    ordering = ("order",)
    fields = (
        "order", "action", "selector", "value_source", "static_value",
        "url_source", "static_url", "iframe_selector", "timeout_ms", "force_click"
    )
    formfield_overrides = {
        forms.CharField: {'widget': forms.TextInput(attrs={'size': '20'})},
    }


@admin.register(DistributionDriver)
class DistributionDriverAdmin(admin.ModelAdmin):
    form = DistributionDriverForm
    list_display = ("name", "driver_type", "organization_id", "status", "created_at")
    list_filter = ("status", "driver_type")
    search_fields = ("name", "organization_id")


@admin.register(HoroshopManifest)
class HoroshopManifestAdmin(admin.ModelAdmin):
    form = HoroshopManifestForm
    list_display = ("driver", "product_schema_id", "event_type", "created_at")
    list_filter = ("driver", "event_type")
    search_fields = ("product_schema_id",)
    inlines = [HoroshopStepInline]


@admin.register(DistributionTask)
class DistributionTaskAdmin(admin.ModelAdmin):
    list_display = ("product_id", "driver", "status", "published_at", "created_at")
    list_filter = ("status", "driver")
    search_fields = ("product_id",)
