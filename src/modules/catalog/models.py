"""Re-export domain models so Django can discover them for migrations."""
from modules.catalog.domain.product import Product  # noqa: F401
from modules.catalog.domain.product_schema import ProductSchema  # noqa: F401
from modules.catalog.domain.product_schema_field import ProductSchemaField  # noqa: F401
from modules.catalog.domain.static_reference import StaticReference  # noqa: F401
from modules.catalog.domain.static_reference_group import StaticReferenceGroup  # noqa: F401
