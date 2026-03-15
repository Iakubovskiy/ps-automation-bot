"""Root URL configuration for the PIM platform."""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

# Action controller routers
from modules.interface.web_interface.actions.product.list_products_action import (
    router as list_products_router,
)
from modules.interface.web_interface.actions.product.get_product_action import (
    router as get_product_router,
)
from modules.interface.web_interface.actions.product.create_product_action import (
    router as create_product_router,
)
from modules.interface.web_interface.actions.product_schema.list_product_schemas_action import (
    router as list_product_schemas_router,
)
from modules.interface.web_interface.actions.product_schema.get_product_schema_action import (
    router as get_product_schema_router,
)
from modules.interface.web_interface.actions.static_reference.list_static_references_action import (
    router as list_static_refs_router,
)
from modules.distribution.infrastructure.integrations.rozetka.rozetka_feed_view import (
    rozetka_feed_view,
)

api = NinjaAPI(
    title="Multi-Marketplace Hub API",
    version="1.0.0",
    description="PIM SaaS Platform API",
)

# Register action routers
api.add_router("", list_products_router)
api.add_router("", get_product_router)
api.add_router("", create_product_router)
api.add_router("", list_product_schemas_router)
api.add_router("", get_product_schema_router)
api.add_router("", list_static_refs_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("feed/rozetka/<str:feed_token>/", rozetka_feed_view, name="rozetka_feed"),
]
