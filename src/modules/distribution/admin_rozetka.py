"""Django Admin registration for Rozetka integration models."""
import json

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from modules.distribution.domain.integrations.rozetka.rozetka_feed_config import RozetkaFeedConfig
from modules.distribution.domain.integrations.rozetka.rozetka_category_mapping import RozetkaCategoryMapping
from modules.distribution.domain.integrations.rozetka.rozetka_field_mapping import RozetkaFieldMapping


class RozetkaCategoryMappingInline(admin.TabularInline):
    model = RozetkaCategoryMapping
    extra = 1
    fields = ("product_schema", "rozetka_category_id", "rozetka_category_name", "is_default")


class RozetkaFieldMappingForm(forms.ModelForm):
    """Form with dynamic attribute_key dropdown based on product_schema."""

    attribute_key = forms.ChoiceField(
        choices=[("", "---------")],
        required=True,
        help_text="Attribute key from the selected product schema",
    )

    class Meta:
        model = RozetkaFieldMapping
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from modules.catalog.domain.product_schema_field import ProductSchemaField

        all_choices = [("", "---------")]
        seen = set()

        # 1. Direct schema field keys
        schema_fields = list(
            ProductSchemaField.objects
            .select_related("source_ref_group")
            .order_by("order", "pk")
        )

        for sf in schema_fields:
            if sf.key not in seen:
                all_choices.append((sf.key, f"{sf.key} ({sf.label})"))
                seen.add(sf.key)

            # 2. Auto-filled keys from StaticReferenceGroup.field_schema
            if sf.auto_fill_from_value and sf.source_ref_group:
                field_schema = sf.source_ref_group.field_schema or []
                for entry in field_schema:
                    k = entry.get("key", "")
                    lbl = entry.get("label", k)
                    if k and k not in seen:
                        all_choices.append((k, f"{k} ({lbl}) [auto-fill]"))
                        seen.add(k)

        self.fields["attribute_key"].choices = all_choices

        # Ensure current value is in choices for existing instances
        if self.instance and self.instance.pk and self.instance.attribute_key:
            current = self.instance.attribute_key
            if current not in seen:
                all_choices.append((current, current))
                self.fields["attribute_key"].choices = all_choices


class RozetkaFieldMappingInline(admin.TabularInline):
    model = RozetkaFieldMapping
    form = RozetkaFieldMappingForm
    extra = 1
    fields = ("product_schema", "attribute_key", "rozetka_field", "param_name")


@admin.register(RozetkaFeedConfig)
class RozetkaFeedConfigAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "driver", "feed_token_short", "created_at")
    readonly_fields = ("feed_token", "feed_url_display")
    fieldsets = (
        (None, {
            "fields": (
                "driver",
                "shop_name",
                "shop_url",
                "currency",
                "media_base_url",
            ),
        }),
        ("Defaults & Validation", {
            "fields": (
                "default_vendor",
                "default_stock_quantity",
                "name_template",
            ),
        }),
        ("AI Instructions (appended to system_prompt)", {
            "classes": ("collapse",),
            "fields": (
                "rozetka_name_instructions",
                "rozetka_description_instructions",
            ),
        }),
        ("Feed Access", {
            "fields": (
                "feed_token",
                "feed_url_display",
            ),
        }),
    )
    inlines = [RozetkaCategoryMappingInline, RozetkaFieldMappingInline]

    @admin.display(description="Token")
    def feed_token_short(self, obj):
        return obj.feed_token[:12] + "..." if obj.feed_token else ""

    @admin.display(description="Feed URL")
    def feed_url_display(self, obj):
        if obj.feed_token:
            return reverse("rozetka_feed", kwargs={"feed_token": obj.feed_token})
        return "—"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["schema_keys_json"] = self._get_schema_keys_json()
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["schema_keys_json"] = self._get_schema_keys_json()
        return super().add_view(request, form_url, extra_context)

    def _get_schema_keys_json(self):
        from modules.catalog.domain.product_schema_field import ProductSchemaField
        schema_keys = {}
        for sf in (
            ProductSchemaField.objects
            .select_related("source_ref_group")
            .order_by("order", "pk")
        ):
            sid = str(sf.product_schema_id)
            schema_keys.setdefault(sid, []).append({"key": sf.key, "label": sf.label})

            # Include auto-filled keys from the linked StaticReferenceGroup
            if sf.auto_fill_from_value and sf.source_ref_group:
                for entry in (sf.source_ref_group.field_schema or []):
                    k = entry.get("key", "")
                    lbl = entry.get("label", k)
                    if k:
                        schema_keys[sid].append({"key": k, "label": f"{lbl} [auto-fill]"})

        return mark_safe(json.dumps(schema_keys))
