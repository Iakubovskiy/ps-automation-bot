"""ProductSchema admin — inline attribute schema editing."""
from django.contrib import admin

from modules.catalog.domain.product_schema import ProductSchema
from modules.catalog.domain.product_schema_field import ProductSchemaField
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


class ProductSchemaFieldInline(admin.TabularInline):
    model = ProductSchemaField
    extra = 1
    fields = (
        "order",
        "key",
        "label",
        "source_type",
        "data_type",
        "source_ref_group",
        "multi_select",
        "auto_fill_from_value",
        "optional",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter source_ref_group dropdown by the parent schema's organization."""
        if db_field.name == "source_ref_group":
            parent_id = request.resolver_match.kwargs.get("object_id")
            if parent_id:
                try:
                    schema = ProductSchema.objects.get(pk=parent_id)
                    kwargs["queryset"] = StaticReferenceGroup.objects.filter(
                        organization=schema.organization,
                    )
                except ProductSchema.DoesNotExist:
                    kwargs["queryset"] = StaticReferenceGroup.objects.none()
            else:
                # New schema — no org yet, show empty dropdown
                kwargs["queryset"] = StaticReferenceGroup.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProductSchema)
class ProductSchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "field_count", "id")
    list_filter = ("organization",)
    search_fields = ("name",)
    fields = ("organization", "name", "system_prompt")
    inlines = [ProductSchemaFieldInline]

    @admin.display(description="Fields")
    def field_count(self, obj):
        return obj.fields.count()
