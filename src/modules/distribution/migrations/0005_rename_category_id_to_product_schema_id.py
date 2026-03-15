"""Rename HoroshopManifest.category_id → product_schema_id."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("distribution", "0004_alter_horoshopstep_action"),
        ("catalog", "0006_rename_category_to_productschema"),
    ]

    operations = [
        migrations.RenameField(
            model_name="horoshopmanifest",
            old_name="category_id",
            new_name="product_schema_id",
        ),
        migrations.AlterUniqueTogether(
            name="horoshopmanifest",
            unique_together={("driver", "product_schema_id", "event_type")},
        ),
    ]
