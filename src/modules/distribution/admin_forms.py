"""Admin form classes for Distribution module."""
from django import forms
from django.apps import apps

from modules.distribution.domain.distribution_driver import DistributionDriver
from modules.distribution.domain.integrations.horoshop.horoshop_manifest import HoroshopManifest


class DistributionDriverForm(forms.ModelForm):
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
            ("rozetka", "Rozetka XML Feed"),
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
            self.fields["organization_id"].choices = [("", "Помилка завантаження")]


class HoroshopManifestForm(forms.ModelForm):
    product_schema_id = forms.ChoiceField(
        label="Схема продукту (Product Schema)",
        help_text="Схема продукту, для якої діє цей маніфест",
        choices=[]
    )

    class Meta:
        model = HoroshopManifest
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            ProductSchema = apps.get_model("catalog", "ProductSchema")
            Organization = apps.get_model("users", "Organization")
            org_dict = {str(org.id): org.name for org in Organization.objects.all()}

            schemas = ProductSchema.objects.all()
            schema_choices = []
            for schema in schemas:
                org_id = str(getattr(schema, "organization_id", ""))
                org_name = org_dict.get(org_id, "Невідома організація")
                label = f"{schema.name} ({org_name})"
                schema_choices.append((str(schema.id), label))
            self.fields["product_schema_id"].choices = sorted(schema_choices, key=lambda x: x[1])

            driver_field = self.fields.get("driver")
            if driver_field:
                driver_choices = [("", "---------")]
                for d in driver_field.queryset:
                    org_name = org_dict.get(str(d.organization_id), "Невідома організація")
                    label = f"{d.name} ({d.driver_type}) — {org_name}"
                    driver_choices.append((d.id, label))
                self.fields["driver"].choices = sorted(driver_choices, key=lambda x: x[1])
        except LookupError:
            self.fields["product_schema_id"].choices = [("", "Помилка завантаження")]
