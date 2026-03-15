"""Add default_vendor, default_stock_quantity, name_template, and AI instruction fields to RozetkaFeedConfig."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("distribution", "0006_rozetka_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="rozetkafeedconfig",
            name="default_vendor",
            field=models.CharField(
                blank=True,
                default="Без бренду",
                help_text="Default vendor when product has no vendor mapped (Rozetka requires this)",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="rozetkafeedconfig",
            name="default_stock_quantity",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Default stock_quantity when not mapped on a product (0 = out of stock)",
            ),
        ),
        migrations.AddField(
            model_name="rozetkafeedconfig",
            name="name_template",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Template for building <name>. Uses {field} placeholders from mapped attributes. "
                    "Special: {vendor}, {article}, {param:Назва параметру}. "
                    "Example: {product_type} {vendor} {model} {param:Довжина клинка} мм {article}"
                ),
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="rozetkafeedconfig",
            name="rozetka_name_instructions",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Extra AI prompt instructions for generating Rozetka-compliant product names. "
                    "Appended to system_prompt when generating AI content."
                ),
            ),
        ),
        migrations.AddField(
            model_name="rozetkafeedconfig",
            name="rozetka_description_instructions",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Extra AI prompt instructions for generating Rozetka-compliant descriptions."
                ),
            ),
        ),
    ]
