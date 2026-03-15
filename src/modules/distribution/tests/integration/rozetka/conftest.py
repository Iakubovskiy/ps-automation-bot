"""Shared tests fixtures for Rozetka tests."""

VALID_CATEGORIES = {1001, 1002, 1003}


def make_offer(
    offer_id="tests-id-1",
    name="Ніж мисливський Prosta Stal",
    vendor="Prosta Stal",
    price="1500",
    stock_quantity="10",
    category_id=1001,
    params=None,
    description="",
    article="",
    **extra_fields,
):
    fm = {
        "name": name,
        "vendor": vendor,
        "price": price,
        "stock_quantity": stock_quantity,
    }
    if description:
        fm["description"] = description
    if article:
        fm["article"] = article
    fm.update(extra_fields)

    return {
        "id": offer_id,
        "available": True,
        "category_id": category_id,
        "field_mappings": fm,
        "param_mappings": params or [],
        "photo_s3_keys": [],
    }
