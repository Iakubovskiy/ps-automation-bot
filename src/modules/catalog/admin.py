"""Django Admin registration for Catalog module — imports from separate files."""
from django.contrib import admin

from modules.catalog.domain.product import Product

from modules.catalog.admin_product_schema import *  # noqa: F401, F403
from modules.catalog.admin_static_reference import *  # noqa: F401, F403


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product_schema", "organization_id", "status", "created_at")
    list_filter = ("status", "product_schema")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")
