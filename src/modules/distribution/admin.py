"""Django Admin registration for Distribution module models."""
from django.contrib import admin

from modules.distribution.domain.distribution_driver import DistributionDriver
from modules.distribution.domain.distribution_manifest import DistributionManifest


@admin.register(DistributionDriver)
class DistributionDriverAdmin(admin.ModelAdmin):
    list_display = ("name", "driver_type", "organization_id", "status", "created_at")
    list_filter = ("status", "driver_type")
    search_fields = ("name",)


@admin.register(DistributionManifest)
class DistributionManifestAdmin(admin.ModelAdmin):
    list_display = ("product_id", "driver", "status", "published_at", "created_at")
    list_filter = ("status",)
    search_fields = ("product_id",)
