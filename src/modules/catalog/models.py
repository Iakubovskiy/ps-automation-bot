"""Re-export domain models so Django can discover them for migrations."""
from modules.catalog.domain.product import Product  # noqa: F401
from modules.catalog.domain.category import Category  # noqa: F401
from modules.catalog.domain.category_attribute import CategoryAttribute  # noqa: F401
from modules.catalog.domain.static_reference import StaticReference  # noqa: F401
from modules.catalog.domain.static_reference_group import StaticReferenceGroup  # noqa: F401
