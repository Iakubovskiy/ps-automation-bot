"""Tests for Rozetka XML renderer — feed structure."""
import xml.etree.ElementTree as ET

from modules.distribution.infrastructure.integrations.rozetka.rozetka_xml_renderer import (
    render_rozetka_feed,
)


def _parse_xml(xml_str: str) -> ET.Element:
    return ET.fromstring(xml_str)


def _render(**kwargs):
    defaults = dict(
        shop_name="Shop", shop_url="", currency="UAH",
        media_base_url="https://cdn.test.com", categories=[], offers=[],
    )
    defaults.update(kwargs)
    return render_rozetka_feed(**defaults)


class TestFeedStructure:
    def test_empty_feed(self):
        xml = _render(shop_name="Test Shop", shop_url="https://test.com")
        root = _parse_xml(xml)
        assert root.tag == "yml_catalog"
        shop = root.find("shop")
        assert shop.find("name").text == "Test Shop"
        assert shop.find("url").text == "https://test.com"
        currencies = shop.find("currencies")
        assert currencies.find("currency").get("id") == "UAH"
        assert list(shop.find("offers")) == []

    def test_xml_declaration(self):
        xml = _render()
        assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_no_url_when_empty(self):
        root = _parse_xml(_render())
        assert root.find(".//shop/url") is None

    def test_categories_rendered(self):
        xml = _render(categories=[
            {"id": 101, "name": "Ножі"},
            {"id": 202, "name": "Сокири"},
        ])
        root = _parse_xml(xml)
        cats = root.findall(".//categories/category")
        assert len(cats) == 2
        assert cats[0].get("id") == "101"
        assert cats[0].text == "Ножі"
        assert cats[1].text == "Сокири"

    def test_multiple_offers(self):
        offers = [
            {
                "id": f"id-{i}", "available": True, "category_id": 101,
                "field_mappings": {"name": f"Ніж {i}", "price": str(100 * i)},
                "param_mappings": [], "photo_s3_keys": [],
            }
            for i in range(5)
        ]
        root = _parse_xml(_render(
            categories=[{"id": 101, "name": "Ножі"}], offers=offers,
        ))
        assert len(root.findall(".//offers/offer")) == 5
