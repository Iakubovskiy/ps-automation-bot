"""Repository for ProductSchema queries.

Provides both sync and async interfaces.
"""
from modules.catalog.domain.product_schema import ProductSchema


class ProductSchemaRepository:
    """Query interface for ProductSchema entities."""

    @staticmethod
    def find_all() -> list[ProductSchema]:
        return list(ProductSchema.objects.all().order_by("name"))

    @staticmethod
    async def afind_all() -> list[ProductSchema]:
        return [c async for c in ProductSchema.objects.all().order_by("name")]

    @staticmethod
    def find_by_organization(organization_id: str) -> list[ProductSchema]:
        return list(
            ProductSchema.objects.filter(organization_id=organization_id).order_by("name")
        )

    @staticmethod
    async def afind_by_organization(organization_id: str) -> list[ProductSchema]:
        return [
            c async for c in
            ProductSchema.objects.filter(organization_id=organization_id).order_by("name")
        ]

    @staticmethod
    def find_by_id(product_schema_id: int) -> ProductSchema | None:
        return ProductSchema.objects.filter(pk=product_schema_id).first()

    @staticmethod
    async def afind_by_id(product_schema_id: int) -> ProductSchema | None:
        return await ProductSchema.objects.filter(pk=product_schema_id).afirst()

    @staticmethod
    def find_by_name(organization_id: str, name: str) -> ProductSchema | None:
        return ProductSchema.objects.filter(
            organization_id=organization_id, name=name,
        ).first()

    @staticmethod
    async def afind_by_name(organization_id: str, name: str) -> ProductSchema | None:
        return await ProductSchema.objects.filter(
            organization_id=organization_id, name=name,
        ).afirst()
