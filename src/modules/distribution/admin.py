"""Django Admin registration for Distribution module models."""
from django.contrib import admin
from django import forms
from django.apps import apps

from modules.distribution.domain.distribution_driver import DistributionDriver
from modules.distribution.domain.distribution_task import DistributionTask
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest
from modules.distribution.domain.integrations.horoshop.horoshop_step import HoroshopStep


class DistributionDriverForm(forms.ModelForm):
    """Кастомна форма для вибору організації та типу драйвера."""

    organization_id = forms.ChoiceField(
        label="Організація",
        help_text="Оберіть організацію, якій належить ця інтеграція",
        choices=[]
    )

    driver_type = forms.ChoiceField(
        label="Тип інтеграції (Driver Type)",
        help_text="Оберіть платформу для публікації",
        choices=[
            ("horoshop", "Horoshop Playwright"),
        ]
    )

    class Meta:
        model = DistributionDriver
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            Organization = apps.get_model("users", "Organization")
            orgs = Organization.objects.all()
            self.fields["organization_id"].choices = [
                (str(org.id), org.name) for org in orgs
            ]
        except LookupError:
            self.fields["organization_id"].choices = [("", "Помилка завантаження організацій")]


class HoroshopManifestForm(forms.ModelForm):
    category_id = forms.ChoiceField(
        label="Категорія (Category)",
        help_text="Категорія товарів, для якої діє цей маніфест",
        choices=[]
    )

    class Meta:
        model = HoroshopManifest
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            Category = apps.get_model("catalog", "Category")
            Organization = apps.get_model("users", "Organization")
            org_dict = {str(org.id): org.name for org in Organization.objects.all()}

            categories = Category.objects.all()
            cat_choices = []
            for cat in categories:
                org_id = str(getattr(cat, "organization_id", ""))
                org_name = org_dict.get(org_id, "Невідома організація")
                label = f"{cat.name} ({org_name})"
                cat_choices.append((str(cat.id), label))
            self.fields["category_id"].choices = sorted(cat_choices, key=lambda x: x[1])

            driver_field = self.fields.get("driver")
            if driver_field:
                driver_choices = [("", "---------")]
                for d in driver_field.queryset:
                    org_name = org_dict.get(str(d.organization_id), "Невідома організація")
                    label = f"{d.name} ({d.driver_type}) — {org_name}"
                    driver_choices.append((d.id, label))
                self.fields["driver"].choices = sorted(driver_choices, key=lambda x: x[1])

        except LookupError:
            self.fields["category_id"].choices = [("", "Помилка завантаження")]

class HoroshopStepInline(admin.TabularInline):
    """Табличне відображення кроків Playwright всередині маніфесту."""
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
    list_display = ("driver", "category_id", "event_type", "created_at")
    list_filter = ("driver", "event_type")
    search_fields = ("category_id",)
    inlines = [HoroshopStepInline]


@admin.register(DistributionTask)
class DistributionTaskAdmin(admin.ModelAdmin):
    list_display = ("product_id", "driver", "status", "published_at", "created_at")
    list_filter = ("status", "driver")
    search_fields = ("product_id",)
