"""Rozetka offer validation orchestrator."""
import logging

from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_vendor_sanitizer import VendorSanitizer
from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_name_sanitizer import NameSanitizer
from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_description_sanitizer import DescriptionSanitizer

logger = logging.getLogger(__name__)


def validate_and_sanitize_offers(
    offers: list[dict],
    category_ids: set[int],
    default_vendor: str,
    default_stock_quantity: int,
    name_template: str = "",
) -> list[dict]:
    """Validate and sanitize offers, returning only valid ones."""
    valid_offers = []
    seen_names: dict[str, str] = {}

    for offer in offers:
        offer_id = offer["id"]
        fm = offer.get("field_mappings", {})
        params = offer.get("param_mappings", [])

        if "stock_quantity" not in fm or not str(fm["stock_quantity"]).strip():
            fm["stock_quantity"] = str(default_stock_quantity)

        vendor = fm.get("vendor", "").strip()
        if not vendor:
            fm["vendor"] = default_vendor
            vendor = default_vendor
        vendor = VendorSanitizer.clean(vendor)
        fm["vendor"] = vendor

        if name_template:
            built_name = NameSanitizer.build_from_template(
                name_template, fm, params, offer_id,
            )
            if built_name:
                fm["name"] = built_name

        name = fm.get("name", "").strip()
        if not name:
            logger.warning("Rozetka offer %s: missing name — skipping", offer_id)
            continue

        name = NameSanitizer.sanitize(name, vendor)
        fm["name"] = name

        name_lower = name.lower()
        if name_lower in seen_names:
            logger.warning(
                "Rozetka offer %s: duplicate name '%s' (same as %s)",
                offer_id, name, seen_names[name_lower],
            )
        else:
            seen_names[name_lower] = offer_id

        name_ua = fm.get("name_ua", "").strip()
        if name_ua:
            fm["name_ua"] = NameSanitizer.sanitize(name_ua, vendor)

        cat_id = offer.get("category_id")
        if cat_id not in category_ids:
            logger.warning(
                "Rozetka offer %s: categoryId %s not in declared categories — skipping",
                offer_id, cat_id,
            )
            continue

        if not params:
            logger.warning(
                "Rozetka offer %s: no params — won't appear in Rozetka filters",
                offer_id,
            )

        price = fm.get("price", "")
        if not str(price).strip():
            logger.warning("Rozetka offer %s: missing price — skipping", offer_id)
            continue

        article = fm.get("article", "").strip()
        if not article:
            logger.warning(
                "Rozetka offer %s: missing article (vendorCode) — recommended",
                offer_id,
            )

        for desc_key in ("description", "description_ua"):
            desc = fm.get(desc_key, "")
            if desc:
                fm[desc_key] = DescriptionSanitizer.sanitize(str(desc), offer_id)

        offer["field_mappings"] = fm
        valid_offers.append(offer)

    skipped = len(offers) - len(valid_offers)
    if skipped:
        logger.info(
            "Rozetka feed: %d offers skipped, %d valid", skipped, len(valid_offers),
        )

    return valid_offers
