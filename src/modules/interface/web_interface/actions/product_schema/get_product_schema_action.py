"""Action: Get a single product schema by ID."""
from ninja import Router, Schema
from typing import Any
from django.shortcuts import get_object_or_404

from modules.catalog.domain.product_schema import ProductSchema

router = Router()


class ProductSchemaDetailSchema(Schema):
    """Full product schema detail response."""

    id: int
    name: str
    system_prompt: str
    attribute_schema: list[dict[str, Any]]


@router.get("/product-schemas/{product_schema_id}", response=ProductSchemaDetailSchema, tags=["Product Schemas"])
def get_product_schema(request, product_schema_id: int):
    """Get a single product schema by ID."""
    schema = get_object_or_404(ProductSchema, pk=product_schema_id)
    return ProductSchemaDetailSchema(
        id=schema.id,
        name=schema.name,
        system_prompt=schema.system_prompt,
        attribute_schema=schema.attribute_schema,
    )
