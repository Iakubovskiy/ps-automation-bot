"""Re-export domain models so Django can discover them for migrations."""
from modules.catalog.domain.product import Product  # noqa: F401
from modules.catalog.domain.category import Category  # noqa: F401
from modules.catalog.domain.static_reference import StaticReference  # noqa: F401
