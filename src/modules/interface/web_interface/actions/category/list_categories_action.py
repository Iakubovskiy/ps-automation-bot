"""Action: List all categories."""
from ninja import Router, Schema
from typing import Any

from modules.catalog.infrastructure.category_repository import CategoryRepository

router = Router()


class CategoryListItemSchema(Schema):
    """Response schema for a category list item."""

    id: int
    name: str
    attribute_schema: list[dict[str, Any]]


@router.get("/categories", response=list[CategoryListItemSchema], tags=["Categories"])
def list_categories(request):
    """List all available categories."""
    categories = CategoryRepository.find_all()
    return [
        CategoryListItemSchema(
            id=c.id,
            name=c.name,
            attribute_schema=c.attribute_schema,
        )
        for c in categories
    ]
