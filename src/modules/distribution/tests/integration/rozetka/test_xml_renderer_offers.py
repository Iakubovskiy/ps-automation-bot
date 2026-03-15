"""Tests for Rozetka XML renderer — offer fields, photos, params, CDATA."""
import xml.etree.ElementTree as ET

from modules.distribution.infrastructure.integrations.rozetka.rozetka_xml_renderer import (
    render_rozetka_feed,
)

_CATEGORIES = [{"id": 101, "name": "Ножі"}]


def _parse_xml(xml_str: str) -> ET.Element:
    return ET.fromstring(xml_str)


def _render_offer(offer: dict) -> str:
    return render_rozetka_feed(
        shop_name="Shop", shop_url="", currency="UAH",
        media_base_url="https://cdn.test.com",
        categories=_CATEGORIES, offers=[offer],
    )


def _base_offer(**overrides) -> dict:
    offer = {
        "id": "abc-123", "available": True, "category_id": 101,
        "field_mappings": {"name": "Ніж", "price": "100"},
        "param_mappings": [], "photo_s3_keys": [],
    }
    offer.update(overrides)
    return offer


class TestOfferFields:
    def test_basic_fields(self):
        offer = _base_offer(field_mappings={
            "name": "Ніж мисливський", "vendor": "Prosta Stal",
            "price": "1500", "stock_quantity": "10", "article": "PSK-001",
        })
        root = _parse_xml(_render_offer(offer))
        o = root.find(".//offers/offer")
        assert o.get("id") == "abc-123"
        assert o.get("available") == "true"
        assert o.find("categoryId").text == "101"
        assert o.find("name").text == "Ніж мисливський"
        assert o.find("vendor").text == "Prosta Stal"
        assert o.find("price").text == "1500"
        assert o.find("stock_quantity").text == "10"
        assert o.find("vendorCode").text == "PSK-001"

    def test_unavailable(self):
        offer = _base_offer(available=False)
        root = _parse_xml(_render_offer(offer))
        assert root.find(".//offers/offer").get("available") == "false"


class TestPhotos:
    def test_photos_rendered(self):
        offer = _base_offer(photo_s3_keys=["photo1.jpg", "photo2.jpg"])
        xml = render_rozetka_feed(
            shop_name="Shop", shop_url="", currency="UAH",
            media_base_url="https://cdn.test.com/",
            categories=_CATEGORIES, offers=[offer],
        )
        pics = _parse_xml(xml).findall(".//offer/picture")
        assert len(pics) == 2
        assert pics[0].text == "https://cdn.test.com/photo1.jpg"

    def test_photos_max_15(self):
        offer = _base_offer(photo_s3_keys=[f"photo{i}.jpg" for i in range(20)])
        root = _parse_xml(_render_offer(offer))
        assert len(root.findall(".//offer/picture")) == 15


class TestParams:
    def test_params_rendered(self):
        offer = _base_offer(param_mappings=[
            ("Сталь", "95Х18"), ("Довжина клинка", "120"),
        ])
        root = _parse_xml(_render_offer(offer))
        params = root.findall(".//offer/param")
        assert len(params) == 2
        assert params[0].get("name") == "Сталь"
        assert params[0].text == "95Х18"

    def test_list_param_joined(self):
        offer = _base_offer(param_mappings=[("Матеріал", ["дерево", "шкіра"])])
        root = _parse_xml(_render_offer(offer))
        assert root.find(".//offer/param").text == "дерево, шкіра"

    def test_empty_param_skipped(self):
        offer = _base_offer(param_mappings=[
            ("Сталь", "95Х18"), ("Порожній", ""), ("Пробіл", "   "),
        ])
        root = _parse_xml(_render_offer(offer))
        params = root.findall(".//offer/param")
        assert len(params) == 1
        assert params[0].get("name") == "Сталь"


class TestCDATA:
    def test_description_in_cdata(self):
        offer = _base_offer(field_mappings={
            "name": "Ніж", "price": "100",
            "description": "Чудовий ніж <b>ручної роботи</b>",
        })
        xml = _render_offer(offer)
        assert "<![CDATA[" in xml
        assert "ручної роботи" in xml
