"""Action: Get a single product by ID."""
from ninja import Router, Schema
from typing import Any
from django.shortcuts import get_object_or_404

from modules.catalog.domain.product import Product

router = Router()


class ProductDetailSchema(Schema):
    """Full product detail response."""

    id: str
    organization_id: str
    category_id: int
    status: str
    attributes: dict[str, Any]
    created_at: str
    updated_at: str


@router.get("/products/{product_id}", response=ProductDetailSchema, tags=["Products"])
def get_product(request, product_id: str):
    """Get a single product by UUID."""
    product = get_object_or_404(Product, pk=product_id)
    return ProductDetailSchema(
        id=str(product.id),
        organization_id=str(product.organization_id),
        category_id=product.category_id,
        status=product.status,
        attributes=product.attributes,
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat(),
    )
