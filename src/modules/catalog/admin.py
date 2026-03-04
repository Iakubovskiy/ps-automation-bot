"""Django Admin registration for Catalog module models."""
from django import forms
from django.contrib import admin

from modules.catalog.domain.category import Category
from modules.catalog.domain.product import Product
from modules.catalog.domain.static_reference import StaticReference
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "id")
    list_filter = ("organization",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("__str__", "category", "organization_id", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")


# ── Dynamic inline form for StaticReference items ────────────────────

# Map data_type → Django form field
_FIELD_BUILDERS = {
    "str": lambda label: forms.CharField(
        label=label, required=False, widget=forms.TextInput(attrs={"size": 12})
    ),
    "int": lambda label: forms.IntegerField(
        label=label, required=False, widget=forms.NumberInput(attrs={"style": "width:80px"})
    ),
    "float": lambda label: forms.FloatField(
        label=label, required=False, widget=forms.NumberInput(attrs={"style": "width:80px", "step": "0.1"})
    ),
}


def _build_dynamic_form(field_schema: list[dict]):
    """Create a ModelForm subclass with dynamic fields declared at class level.

    Django admin reads fields from the class definition (not __init__),
    so we must build them as class attributes in a dynamic type() call.
    """

    schema_keys = [f["key"] for f in field_schema]

    # Build class-level field dict
    form_fields = {}
    for field_def in field_schema:
        fkey = field_def["key"]
        flabel = field_def.get("label", fkey)
        ftype = field_def.get("data_type", "str")
        builder = _FIELD_BUILDERS.get(ftype, _FIELD_BUILDERS["str"])
        form_fields[fkey] = builder(flabel)

    class DynamicRefForm(forms.ModelForm):
        class Meta:
            model = StaticReference
            fields = ("key", "label")

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.pk:
                val = self.instance.value or {}
                for fkey in schema_keys:
                    if fkey in val:
                        self.initial[fkey] = val[fkey]

        def save(self, commit=True):
            """Pack dynamic fields back into the value JSON."""
            instance = super().save(commit=False)
            value = instance.value if isinstance(instance.value, dict) else {}
            for fkey in schema_keys:
                v = self.cleaned_data.get(fkey)
                if v is not None and v != "":
                    value[fkey] = v
                elif fkey in value:
                    del value[fkey]
            instance.value = value
            if commit:
                instance.save()
            return instance

    for fkey, field_obj in form_fields.items():
        DynamicRefForm.declared_fields[fkey] = field_obj
        DynamicRefForm.base_fields[fkey] = field_obj

    return DynamicRefForm


class StaticReferenceInline(admin.TabularInline):
    """Inline editor — dynamically builds columns from group's field_schema."""

    model = StaticReference
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        if obj and obj.field_schema:
            kwargs["form"] = _build_dynamic_form(obj.field_schema)
        else:
            kwargs["form"] = type(
                "BasicRefForm",
                (forms.ModelForm,),
                {"Meta": type("Meta", (), {"model": StaticReference, "fields": ("key", "label", "value")})},
            )
        return super().get_formset(request, obj, **kwargs)


@admin.register(StaticReferenceGroup)
class StaticReferenceGroupAdmin(admin.ModelAdmin):
    """Admin for groups — items are edited inline with dynamic fields.

    1. Create the group, define field_schema → Save
    2. Reopen — dynamic columns appear in the inline
    3. Add items with real input fields (no raw JSON needed)
    """

    list_display = ("name", "organization", "item_count")
    list_filter = ("organization",)
    search_fields = ("name",)
    inlines = [StaticReferenceInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()
