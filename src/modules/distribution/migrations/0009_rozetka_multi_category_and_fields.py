"""Add is_default to category mapping, update unique_together,
add new RozetkaField choices, add currency choices."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("distribution", "0008_alter_horoshopmanifest_product_schema_id_and_more"),
        ("catalog", "0006_rename_category_to_productschema"),
    ]

    operations = [
        # Add is_default field to RozetkaCategoryMapping
        migrations.AddField(
            model_name="rozetkacategorymapping",
            name="is_default",
            field=models.BooleanField(
                default=False,
                help_text="Default category for this schema (used when product has no per-product override)",
            ),
        ),
        # Change unique_together: (feed_config, product_schema) → (feed_config, product_schema, rozetka_category_id)
        migrations.AlterUniqueTogether(
            name="rozetkacategorymapping",
            unique_together={("feed_config", "product_schema", "rozetka_category_id")},
        ),
        # Update rozetka_field choices on RozetkaFieldMapping
        migrations.AlterField(
            model_name="rozetkafieldmapping",
            name="rozetka_field",
            field=models.CharField(
                max_length=64,
                choices=[
                    ("name", "name (product title)"),
                    ("name_ua", "name_ua (Ukrainian title)"),
                    ("description", "description (HTML in CDATA)"),
                    ("description_ua", "description_ua (HTML in CDATA)"),
                    ("vendor", "vendor (brand)"),
                    ("price", "price"),
                    ("price_old", "price_old (strikethrough)"),
                    ("price_promo", "price_promo (promo page)"),
                    ("currencyId", "currencyId (UAH/USD/EUR per offer)"),
                    ("stock_quantity", "stock_quantity"),
                    ("article", "article (vendorCode / SKU)"),
                    ("model", "model"),
                    ("url", "url (product page link)"),
                    ("state", "state (new/used/refurbished/stock)"),
                    ("docket", "docket (short desc, required for used/stock)"),
                    ("docket_ua", "docket_ua"),
                    ("picture", "picture (photo field)"),
                    ("rozetka_category_id", "rozetka_category_id (per-product override)"),
                    ("param", "param (custom parameter)"),
                ],
                help_text="Target XML field in the Rozetka feed",
            ),
        ),
        # Update currency field with choices
        migrations.AlterField(
            model_name="rozetkafeedconfig",
            name="currency",
            field=models.CharField(
                max_length=3,
                default="UAH",
                choices=[
                    ("UAH", "UAH (гривня)"),
                    ("USD", "USD (долар)"),
                    ("EUR", "EUR (євро)"),
                ],
                help_text="Default currency for offers (rate=1). Rozetka supports UAH, USD, EUR.",
            ),
        ),
    ]
