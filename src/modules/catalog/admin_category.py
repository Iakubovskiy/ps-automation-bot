"""Category admin — inline attribute schema editing."""
from django.contrib import admin

from modules.catalog.domain.category import Category
from modules.catalog.domain.category_attribute import CategoryAttribute
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
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
        """Filter source_ref_group dropdown by the parent category's organization."""
        if db_field.name == "source_ref_group":
            parent_id = request.resolver_match.kwargs.get("object_id")
            if parent_id:
                try:
                    category = Category.objects.get(pk=parent_id)
                    kwargs["queryset"] = StaticReferenceGroup.objects.filter(
                        organization=category.organization,
                    )
                except Category.DoesNotExist:
                    kwargs["queryset"] = StaticReferenceGroup.objects.none()
            else:
                # New category — no org yet, show empty dropdown
                kwargs["queryset"] = StaticReferenceGroup.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "attribute_count", "id")
    list_filter = ("organization",)
    search_fields = ("name",)
    fields = ("organization", "name", "system_prompt")
    inlines = [CategoryAttributeInline]

    @admin.display(description="Fields")
    def attribute_count(self, obj):
        return obj.attributes.count()
