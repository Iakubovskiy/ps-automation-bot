"""Action: List all product schemas."""
from ninja import Router, Schema
from typing import Any

from modules.catalog.infrastructure.product_schema_repository import ProductSchemaRepository

router = Router()


class ProductSchemaListItemSchema(Schema):
    """Response schema for a product schema list item."""

    id: int
    name: str
    attribute_schema: list[dict[str, Any]]


@router.get("/product-schemas", response=list[ProductSchemaListItemSchema], tags=["Product Schemas"])
def list_product_schemas(request):
    """List all available product schemas."""
    schemas = ProductSchemaRepository.find_all()
    return [
        ProductSchemaListItemSchema(
            id=s.id,
            name=s.name,
            attribute_schema=s.attribute_schema,
        )
        for s in schemas
    ]
