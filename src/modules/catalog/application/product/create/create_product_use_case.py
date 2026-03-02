"""Use case: Create a new Product from the bot interface.

Validates collected attributes against the Category's attribute_schema
using a dynamically built Pydantic model, then creates the Product entity.
"""
import logging
from typing import Any

from pydantic import ValidationError, create_model

from modules.catalog.application.product.create.dto.create_product_dto import (
    CreateProductDto,
)
from modules.catalog.domain.category import Category
from modules.catalog.domain.product import Product
from modules.catalog.infrastructure.s3_service import S3Service

logger = logging.getLogger(__name__)

# Mapping from attribute_schema data_type strings to Python types
_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "list": list,
}


class CreateProductUseCase:
    """Validates attributes and creates a Product in DRAFT status.

    Flow:
        1. Load the Category and its attribute_schema.
        2. Build a dynamic Pydantic model from the schema.
        3. Validate the incoming attributes against it.
        4. Upload media files to S3.
        5. Create the Product (fires ProductCreatedEvent via the domain model).
    """

    def __init__(self, s3_service: S3Service | None = None):
        self._s3 = s3_service

    def execute(self, dto: CreateProductDto) -> Product:
        """Create and return a new Product.

        Args:
            dto: Validated input from the interface layer.

        Returns:
            The newly created Product instance.

        Raises:
            Category.DoesNotExist: If the category_id is invalid.
            ValidationError: If attributes don't match the schema.
        """
        category = Category.objects.get(pk=dto.category_id)

        # ── Validate attributes against dynamic schema ───────────────
        self._validate_attributes(category, dto.attributes)

        # ── Upload media to S3 if service is available ───────────────
        attributes = dict(dto.attributes)
        if self._s3 and dto.photo_paths:
            # We'll store S3 keys in attributes for later use
            s3_keys = self._s3.upload_product_media(
                product_id=attributes.get("product_code", "temp"),
                local_paths=dto.photo_paths,
            )
            attributes["photo_s3_keys"] = s3_keys

        if dto.video_path:
            attributes["video_path"] = dto.video_path
        if dto.video_url:
            attributes["video_url"] = dto.video_url

        # ── Create the Product (domain model publishes event) ────────
        product = Product.create(
            organization_id=dto.organization_id,
            category=category,
            attributes=attributes,
        )

        logger.info(
            "Created product %s (category=%s, org=%s)",
            product.id,
            category.name,
            dto.organization_id,
        )

        return product

    @staticmethod
    def _validate_attributes(category: Category, attributes: dict[str, Any]) -> None:
        """Build a dynamic Pydantic model from attribute_schema and validate.

        Uses pydantic.create_model() to construct a validation model at runtime.
        Each field in the schema becomes a Pydantic field with the appropriate type.

        Raises:
            ValidationError: If validation fails.
        """
        schema = category.attribute_schema
        if not schema:
            return  # No schema defined — accept anything

        field_definitions: dict[str, tuple] = {}

        for field_spec in schema:
            key = field_spec["key"]
            data_type_str = field_spec.get("data_type", "str")
            python_type = _TYPE_MAP.get(data_type_str, str)

            # Multi-select fields always expect a list
            if field_spec.get("multi_select"):
                python_type = list

            # All fields are optional (default=None) so partial data is allowed
            field_definitions[key] = (python_type | None, None)

        DynamicModel = create_model(
            f"{category.name}AttributeModel",
            **field_definitions,
        )

        try:
            DynamicModel(**attributes)
        except ValidationError:
            logger.error(
                "Attribute validation failed for category '%s': %s",
                category.name,
                attributes,
            )
            raise
