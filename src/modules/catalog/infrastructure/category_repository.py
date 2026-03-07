"""Repository for Category queries.

Provides both sync and async interfaces.
"""
from modules.catalog.domain.category import Category


class CategoryRepository:
    """Query interface for Category entities."""

    @staticmethod
    def find_all() -> list[Category]:
        return list(Category.objects.all().order_by("name"))

    @staticmethod
    async def afind_all() -> list[Category]:
        return [c async for c in Category.objects.all().order_by("name")]

    @staticmethod
    def find_by_organization(organization_id: str) -> list[Category]:
        return list(
            Category.objects.filter(organization_id=organization_id).order_by("name")
        )

    @staticmethod
    async def afind_by_organization(organization_id: str) -> list[Category]:
        return [
            c async for c in
            Category.objects.filter(organization_id=organization_id).order_by("name")
        ]

    @staticmethod
    def find_by_id(category_id: int) -> Category | None:
        return Category.objects.filter(pk=category_id).first()

    @staticmethod
    async def afind_by_id(category_id: int) -> Category | None:
        return await Category.objects.filter(pk=category_id).afirst()

    @staticmethod
    def find_by_name(organization_id: str, name: str) -> Category | None:
        return Category.objects.filter(
            organization_id=organization_id, name=name,
        ).first()

    @staticmethod
    async def afind_by_name(organization_id: str, name: str) -> Category | None:
        return await Category.objects.filter(
            organization_id=organization_id, name=name,
        ).afirst()
