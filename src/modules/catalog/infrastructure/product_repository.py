"""Repository for Product queries.

Wraps Django ORM to provide a clean interface for the application layer.
"""
from modules.catalog.domain.product import Product, ProductStatus


class ProductRepository:
    """Query interface for Product entities."""

    @staticmethod
    def find_by_id(product_id: str) -> Product | None:
        """Look up a product by UUID."""
        return Product.objects.filter(pk=product_id).first()

    @staticmethod
    def find_by_organization(
        organization_id: str,
        status: str | None = None,
    ) -> list[Product]:
        """Return products for an organization, optionally filtered by status."""
        qs = Product.objects.filter(organization_id=organization_id)
        if status:
            qs = qs.filter(status=status)
        return list(qs.order_by("-created_at"))

    @staticmethod
    def find_by_product_schema(
        product_schema_id: int,
        organization_id: str | None = None,
    ) -> list[Product]:
        """Return products for a schema, optionally scoped to an organization."""
        qs = Product.objects.filter(product_schema_id=product_schema_id)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        return list(qs.order_by("-created_at"))

    @staticmethod
    def find_ready(organization_id: str) -> list[Product]:
        """Return all READY products for an organization."""
        return list(
            Product.objects.filter(
                organization_id=organization_id,
                status=ProductStatus.READY,
            ).order_by("-created_at")
        )
