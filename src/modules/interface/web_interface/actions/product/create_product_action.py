"""Action: Create a product via API."""
from ninja import Router, Schema
from typing import Any

from modules.catalog.application.product.create.create_product_use_case import CreateProductUseCase
from modules.catalog.application.product.create.dto.create_product_dto import CreateProductDto

router = Router()


class CreateProductRequestSchema(Schema):
    """Request body for product creation."""

    organization_id: str
    category_id: int
    attributes: dict[str, Any]
    photo_paths: list[str] = []
    video_path: str = ""
    video_url: str = ""


class CreateProductResponseSchema(Schema):
    """Response after product creation."""

    id: str
    status: str


@router.post("/products", response=CreateProductResponseSchema, tags=["Products"])
def create_product(request, payload: CreateProductRequestSchema):
    """Create a new product."""
    dto = CreateProductDto(
        organization_id=payload.organization_id,
        category_id=payload.category_id,
        attributes=payload.attributes,
        photo_paths=payload.photo_paths,
        video_path=payload.video_path,
        video_url=payload.video_url,
    )

    use_case = CreateProductUseCase()
    product = use_case.execute(dto)

    return CreateProductResponseSchema(
        id=str(product.id),
        status=product.status,
    )
