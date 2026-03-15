"""Add Rozetka integration models."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("distribution", "0005_rename_category_id_to_product_schema_id"),
        ("catalog", "0006_rename_category_to_productschema"),
    ]

    operations = [
        migrations.CreateModel(
            name="RozetkaFeedConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "feed_token",
                    models.CharField(
                        db_index=True,
                        help_text="Auto-generated token used in the feed URL for security",
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "shop_name",
                    models.CharField(
                        help_text="Shop name for <name> tag in XML feed",
                        max_length=255,
                    ),
                ),
                (
                    "shop_url",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text="Shop URL for <url> tag in XML feed",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="UAH",
                        help_text="Default currency ID for <currencyId> in XML",
                        max_length=3,
                    ),
                ),
                (
                    "media_base_url",
                    models.URLField(
                        help_text="Base URL prepended to S3 keys for public image URLs",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rozetka_feed_config",
                        to="distribution.distributiondriver",
                    ),
                ),
            ],
            options={
                "db_table": "distribution_rozetka_feed_config",
                "verbose_name": "Rozetka Feed Config",
                "verbose_name_plural": "Rozetka Feed Configs",
            },
        ),
        migrations.CreateModel(
            name="RozetkaCategoryMapping",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rozetka_category_id",
                    models.PositiveIntegerField(
                        help_text="Rozetka's rz_id for this category",
                    ),
                ),
                (
                    "rozetka_category_name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Human-readable Rozetka category name (for admin convenience)",
                        max_length=255,
                    ),
                ),
                (
                    "feed_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_mappings",
                        to="distribution.rozetkafeedconfig",
                    ),
                ),
                (
                    "product_schema",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rozetka_category_mappings",
                        to="catalog.productschema",
                    ),
                ),
            ],
            options={
                "db_table": "distribution_rozetka_category_mapping",
                "verbose_name": "Rozetka Category Mapping",
                "verbose_name_plural": "Rozetka Category Mappings",
                "unique_together": {("feed_config", "product_schema")},
            },
        ),
        migrations.CreateModel(
            name="RozetkaFieldMapping",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "attribute_key",
                    models.CharField(
                        help_text="Key in product.attributes to read the value from",
                        max_length=128,
                    ),
                ),
                (
                    "rozetka_field",
                    models.CharField(
                        choices=[
                            ("name", "name"),
                            ("name_ua", "name_ua"),
                            ("description", "description"),
                            ("description_ua", "description_ua"),
                            ("vendor", "vendor"),
                            ("price", "price"),
                            ("price_old", "price_old"),
                            ("stock_quantity", "stock_quantity"),
                            ("article", "article (vendorCode)"),
                            ("model", "model"),
                            ("state", "state"),
                            ("docket", "docket"),
                            ("docket_ua", "docket_ua"),
                            ("url", "url"),
                            ("param", "param (custom parameter)"),
                        ],
                        help_text="Target XML field in the Rozetka feed",
                        max_length=64,
                    ),
                ),
                (
                    "param_name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text='<param name="..."> when rozetka_field is PARAM',
                        max_length=128,
                    ),
                ),
                (
                    "feed_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="field_mappings",
                        to="distribution.rozetkafeedconfig",
                    ),
                ),
                (
                    "product_schema",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rozetka_field_mappings",
                        to="catalog.productschema",
                    ),
                ),
            ],
            options={
                "db_table": "distribution_rozetka_field_mapping",
                "verbose_name": "Rozetka Field Mapping",
                "verbose_name_plural": "Rozetka Field Mappings",
                "unique_together": {("feed_config", "product_schema", "attribute_key")},
            },
        ),
    ]
