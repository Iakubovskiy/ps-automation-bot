"""Rozetka XML feed endpoint.

Plain Django view (not Django Ninja) that serves the YML feed.
Rozetka crawls this URL periodically.
"""
import logging

from django.http import HttpResponse, Http404

from modules.catalog.domain.product import Product, ProductStatus
from modules.distribution.domain.integrations.rozetka.rozetka_feed_config import RozetkaFeedConfig
from modules.distribution.domain.integrations.rozetka.rozetka_category_mapping import RozetkaCategoryMapping
from modules.distribution.domain.integrations.rozetka.rozetka_field_mapping import RozetkaFieldMapping
from modules.distribution.infrastructure.integrations.rozetka.rozetka_offer_builder import OfferBuilder
from modules.distribution.infrastructure.integrations.rozetka.rozetka_xml_renderer import render_rozetka_feed
from modules.distribution.infrastructure.integrations.rozetka.validation.rozetka_offer_validator import validate_and_sanitize_offers

logger = logging.getLogger(__name__)

XML_CONTENT_TYPE = "application/xml; charset=utf-8"


def rozetka_feed_view(request, feed_token: str) -> HttpResponse:
    """Serve the Rozetka YML XML feed for the given token."""
    config = _load_config(feed_token)
    cat_mappings = list(
        RozetkaCategoryMapping.objects.filter(feed_config=config)
        .select_related("product_schema")
    )

    if not cat_mappings:
        return HttpResponse(_empty_feed(config), content_type=XML_CONTENT_TYPE)

    rz_categories = _build_rz_categories(cat_mappings)
    # Map rz_id → internal sequential id for categoryId in offers
    rz_id_to_internal = {cat["rz_id"]: cat["id"] for cat in rz_categories}

    # One schema can map to multiple rz categories — pick the default one
    schema_to_rz_cat = {}
    for cm in cat_mappings:
        sid = cm.product_schema_id
        if sid not in schema_to_rz_cat or cm.is_default:
            schema_to_rz_cat[sid] = cm.rozetka_category_id

    schema_field_mappings = _load_field_mappings(config)

    products = list(
        Product.objects.filter(
            organization_id=str(config.driver.organization_id),
            status=ProductStatus.READY,
        ).select_related("product_schema")
    )

    offers = OfferBuilder.build_offers(
        products, schema_to_rz_cat, schema_field_mappings, rz_id_to_internal,
    )

    # Validate against internal category IDs
    declared_cat_ids = {cat["id"] for cat in rz_categories}

    offers = validate_and_sanitize_offers(
        offers=offers,
        category_ids=declared_cat_ids,
        default_vendor=config.default_vendor or "Без бренду",
        default_stock_quantity=config.default_stock_quantity,
        name_template=config.name_template,
    )

    xml_content = render_rozetka_feed(
        shop_name=config.shop_name,
        shop_url=config.shop_url,
        currency=config.currency,
        media_base_url=config.media_base_url,
        categories=rz_categories,
        offers=offers,
    )
    return HttpResponse(xml_content, content_type=XML_CONTENT_TYPE)


def _load_config(feed_token: str) -> RozetkaFeedConfig:
    try:
        return RozetkaFeedConfig.objects.select_related("driver").get(
            feed_token=feed_token, driver__status="ACTIVE",
        )
    except RozetkaFeedConfig.DoesNotExist:
        raise Http404("Feed not found")


def _build_rz_categories(cat_mappings: list) -> list[dict]:
    """Build unique category list with sequential IDs and rz_id for Rozetka matching."""
    seen = {}
    categories = []
    counter = 1
    for cm in cat_mappings:
        rz_id = cm.rozetka_category_id
        if rz_id not in seen:
            seen[rz_id] = counter
            categories.append({
                "id": counter,
                "rz_id": rz_id,
                "name": cm.rozetka_category_name or str(rz_id),
            })
            counter += 1
    return categories


def _load_field_mappings(config: RozetkaFeedConfig) -> dict:
    result: dict[int, list] = {}
    for fm in RozetkaFieldMapping.objects.filter(feed_config=config):
        result.setdefault(fm.product_schema_id, []).append(fm)
    return result


def _empty_feed(config: RozetkaFeedConfig) -> str:
    return render_rozetka_feed(
        shop_name=config.shop_name, shop_url=config.shop_url,
        currency=config.currency, media_base_url=config.media_base_url,
        categories=[], offers=[],
    )
