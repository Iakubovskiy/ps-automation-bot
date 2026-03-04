"""Repository for Category queries.

Wraps Django ORM to provide a clean interface for the application layer.
"""
from modules.catalog.domain.category import Category


class CategoryRepository:
    """Query interface for Category entities."""

    @staticmethod
    def find_all() -> list[Category]:
        """Return all categories ordered by name."""
        return list(Category.objects.all().order_by("name"))

    @staticmethod
    def find_by_organization(organization_id: str) -> list[Category]:
        """Return all categories for a specific organization."""
        return list(
            Category.objects.filter(
                organization_id=organization_id,
            ).order_by("name")
        )

    @staticmethod
    def find_by_id(category_id: int) -> Category | None:
        """Look up a category by its primary key."""
        return Category.objects.filter(pk=category_id).first()

    @staticmethod
    def find_by_name(organization_id: str, name: str) -> Category | None:
        """Look up a category by name within an organization."""
        return Category.objects.filter(
            organization_id=organization_id,
            name=name,
        ).first()
