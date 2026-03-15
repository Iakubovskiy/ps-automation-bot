"""Rozetka YML XML feed renderer.

Pure function that takes structured data and produces XML string.
No database access — fully testable without HTTP.
"""
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring


MAX_PHOTOS = 15

# Unique markers for CDATA — ElementTree escapes < and > in text,
# so we use placeholders and post-process after serialization
_CDATA_BEGIN = "\x02CDATA_BEGIN\x02"
_CDATA_END = "\x02CDATA_END\x02"

# Tag mapping: rozetka field key → XML tag name
_FIELD_TO_TAG = {
    "name": "name",
    "name_ua": "name_ua",
    "vendor": "vendor",
    "price": "price",
    "price_old": "price_old",
    "price_promo": "price_promo",
    "currencyId": "currencyId",
    "stock_quantity": "stock_quantity",
    "article": "vendorCode",
    "model": "model",
    "state": "state",
    "docket": "docket",
    "docket_ua": "docket_ua",
    "url": "url",
}


def render_rozetka_feed(
    shop_name: str,
    shop_url: str,
    currency: str,
    media_base_url: str,
    categories: list[dict],
    offers: list[dict],
) -> str:
    """Render a Rozetka YML XML feed. Returns XML string with declaration."""
    root = Element("yml_catalog", date=datetime.now().strftime("%Y-%m-%d %H:%M"))
    shop = SubElement(root, "shop")

    SubElement(shop, "name").text = shop_name
    if shop_url:
        SubElement(shop, "url").text = shop_url

    currencies = SubElement(shop, "currencies")
    SubElement(currencies, "currency", id=currency, rate="1")

    _render_categories(shop, categories)
    _render_offers(shop, offers, media_base_url, currency)

    xml_str = tostring(root, encoding="unicode", xml_declaration=False)
    xml_str = xml_str.replace(_CDATA_BEGIN, "<![CDATA[").replace(_CDATA_END, "]]>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


def _render_categories(shop: Element, categories: list[dict]) -> None:
    cats_el = SubElement(shop, "categories")
    for cat in categories:
        attrs = {"id": str(cat["id"])}
        # rz_id links your category to Rozetka's catalog for auto-matching
        if cat.get("rz_id"):
            attrs["rz_id"] = str(cat["rz_id"])
        cat_el = SubElement(cats_el, "category", **attrs)
        cat_el.text = cat.get("name", "")


def _render_offers(shop: Element, offers: list[dict], media_base_url: str, default_currency: str) -> None:
    offers_el = SubElement(shop, "offers")
    for offer in offers:
        offer_el = SubElement(
            offers_el, "offer",
            id=str(offer["id"]),
            available="true" if offer.get("available", True) else "false",
        )
        SubElement(offer_el, "categoryId").text = str(offer["category_id"])
        fm = offer.get("field_mappings", {})

        # Add default currencyId if not mapped per product
        if "currencyId" not in fm or not str(fm["currencyId"]).strip():
            fm["currencyId"] = default_currency

        for field_key, tag_name in _FIELD_TO_TAG.items():
            value = fm.get(field_key)
            if value is not None and str(value).strip():
                SubElement(offer_el, tag_name).text = str(value)

        for desc_field in ("description", "description_ua"):
            value = fm.get(desc_field)
            if value and str(value).strip():
                el = SubElement(offer_el, desc_field)
                el.text = _CDATA_BEGIN + str(value) + _CDATA_END

        base_url = media_base_url.rstrip("/")
        for key in offer.get("photo_s3_keys", [])[:MAX_PHOTOS]:
            SubElement(offer_el, "picture").text = f"{base_url}/{key}"

        for param_name, param_value in offer.get("param_mappings", []):
            if param_value is not None and str(param_value).strip():
                p_el = SubElement(offer_el, "param", name=param_name)
                if isinstance(param_value, list):
                    p_el.text = ", ".join(str(v) for v in param_value)
                else:
                    p_el.text = str(param_value)
