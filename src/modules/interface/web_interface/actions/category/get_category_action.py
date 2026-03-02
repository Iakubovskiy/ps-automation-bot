"""Action: Get a single category by ID."""
from ninja import Router, Schema
from typing import Any
from django.shortcuts import get_object_or_404

from modules.catalog.domain.category import Category

router = Router()


class CategoryDetailSchema(Schema):
    """Full category detail response."""

    id: int
    name: str
    system_prompt: str
    attribute_schema: list[dict[str, Any]]


@router.get("/categories/{category_id}", response=CategoryDetailSchema, tags=["Categories"])
def get_category(request, category_id: int):
    """Get a single category by ID."""
    category = get_object_or_404(Category, pk=category_id)
    return CategoryDetailSchema(
        id=category.id,
        name=category.name,
        system_prompt=category.system_prompt,
        attribute_schema=category.attribute_schema,
    )
