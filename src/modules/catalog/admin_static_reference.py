"""StaticReferenceGroup admin — dynamic inline items from field_schema."""
from django import forms
from django.contrib import admin

from modules.catalog.domain.static_reference import StaticReference
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


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
    """Create a ModelForm with dynamic fields from group's field_schema."""
    schema_keys = [f["key"] for f in field_schema]

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
    list_display = ("name", "organization", "item_count")
    list_filter = ("organization",)
    search_fields = ("name",)
    inlines = [StaticReferenceInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()
