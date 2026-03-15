"""Rename Category → ProductSchema and CategoryAttribute → ProductSchemaField."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_categoryattribute_optional_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Category",
            new_name="ProductSchema",
        ),
        migrations.RenameModel(
            old_name="CategoryAttribute",
            new_name="ProductSchemaField",
        ),

        migrations.RenameField(
            model_name="productschemafield",
            old_name="category",
            new_name="product_schema",
        ),

        migrations.RenameField(
            model_name="product",
            old_name="category",
            new_name="product_schema",
        ),

        migrations.AlterModelTable(
            name="productschema",
            table="catalog_productschema",
        ),
        migrations.AlterModelTable(
            name="productschemafield",
            table="catalog_productschemafield",
        ),

        migrations.AlterUniqueTogether(
            name="productschemafield",
            unique_together={("product_schema", "key")},
        ),
    ]
