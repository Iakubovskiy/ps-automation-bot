"""Rozetka offer builder.

Transforms Product models + field mappings into offer dicts
ready for validation and XML rendering.
"""
import logging

from modules.distribution.domain.integrations.rozetka.rozetka_field_mapping import RozetkaFieldMapping, RozetkaField

logger = logging.getLogger(__name__)


class OfferBuilder:
    """Builds offer dicts from products and their field mappings."""

    @staticmethod
    def build_offers(
        products: list,
        schema_to_rz_cat: dict[int, int],
        schema_field_mappings: dict[int, list[RozetkaFieldMapping]],
        rz_id_to_internal: dict[int, int],
    ) -> list[dict]:
        """Convert products to offer dicts using field mappings.

        Args:
            products: Product instances with product_schema relation.
            schema_to_rz_cat: Default rz_id per product_schema_id.
            schema_field_mappings: Field mappings per product_schema_id.
            rz_id_to_internal: Maps Rozetka rz_id to internal category ID.
        """
        offers = []
        for product in products:
            default_rz_cat = schema_to_rz_cat.get(product.product_schema_id)
            if default_rz_cat is None:
                continue

            mappings = schema_field_mappings.get(product.product_schema_id, [])
            if not mappings:
                continue

            field_values = {}
            param_values = []
            photo_keys = []
            rz_cat_override = None

            for fm in mappings:
                value = product.attributes.get(fm.attribute_key)
                if value is None:
                    continue

                if fm.rozetka_field == RozetkaField.PARAM:
                    param_values.append((fm.param_name, value))
                elif fm.rozetka_field == RozetkaField.PICTURE:
                    # Support both FILE (string) and FILE_ARRAY (list)
                    if isinstance(value, list):
                        photo_keys.extend(value)
                    elif isinstance(value, str) and value.strip():
                        photo_keys.append(value)
                elif fm.rozetka_field == RozetkaField.CATEGORY_ID:
                    try:
                        rz_cat_override = int(value)
                    except (ValueError, TypeError):
                        pass
                else:
                    field_values[fm.rozetka_field] = value

            # Fallback to legacy photo_s3_keys
            if not photo_keys:
                legacy = product.attributes.get("photo_s3_keys", [])
                if isinstance(legacy, list):
                    photo_keys = legacy

            # Resolve rz_id → internal category ID
            rz_id = rz_cat_override or default_rz_cat
            internal_cat_id = rz_id_to_internal.get(rz_id)
            if internal_cat_id is None:
                logger.warning(
                    "Product %s: rz_id %s not in declared categories — skipping",
                    product.id, rz_id,
                )
                continue

            offers.append({
                "id": str(product.id),
                "available": True,
                "category_id": internal_cat_id,
                "field_mappings": field_values,
                "param_mappings": param_values,
                "photo_s3_keys": photo_keys,
            })

        return offers
