"""DTO for creating a new Product from the bot interface."""
from typing import Any

from pydantic import BaseModel


class CreateProductDto(BaseModel):
    """Data required to create a new Product.

    Attributes:
        organization_id: UUID of the Organization this product belongs to.
        category_id: PK of the Category defining the attribute schema.
        attributes: Collected attribute values (validated against the schema).
        photo_paths: Local file paths for product photos.
        video_path: Optional local path for a product video.
        video_url: Optional YouTube URL.
    """

    organization_id: str
    category_id: int
    attributes: dict[str, Any]
    photo_paths: list[str] = []
    video_path: str = ""
    video_url: str = ""
