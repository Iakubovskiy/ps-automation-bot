"""Action: List all products for an organization."""
from ninja import Router, Schema
from typing import Any

from modules.catalog.infrastructure.product_repository import ProductRepository

router = Router()


class ProductListItemSchema(Schema):
    """Response schema for a product list item."""

    id: str
    category_id: int
    status: str
    attributes: dict[str, Any]
    created_at: str


@router.get("/products", response=list[ProductListItemSchema], tags=["Products"])
def list_products(request, organization_id: str, status: str = None):
    """List products for an organization, optionally filtered by status."""
    products = ProductRepository.find_by_organization(
        organization_id=organization_id,
        status=status,
    )
    return [
        ProductListItemSchema(
            id=str(p.id),
            category_id=p.category_id,
            status=p.status,
            attributes=p.attributes,
            created_at=p.created_at.isoformat(),
        )
        for p in products
    ]
