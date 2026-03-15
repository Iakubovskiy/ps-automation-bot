"""Tests for the main offer validation pipeline."""
import pytest

from modules.distribution.infrastructure.integrations.rozetka.validation.rozetka_offer_validator import (
    validate_and_sanitize_offers,
)
from modules.distribution.tests.integration.rozetka.conftest import make_offer, VALID_CATEGORIES


class TestValidateAndSanitize:
    def test_valid_offer_passes(self):
        offers = [make_offer()]
        result = validate_and_sanitize_offers(offers, VALID_CATEGORIES, "Без бренду", 1)
        assert len(result) == 1
        assert result[0]["id"] == "tests-id-1"

    def test_missing_name_skipped(self):
        result = validate_and_sanitize_offers(
            [make_offer(name="")], VALID_CATEGORIES, "Без бренду", 1,
        )
        assert len(result) == 0

    def test_missing_price_skipped(self):
        result = validate_and_sanitize_offers(
            [make_offer(price="")], VALID_CATEGORIES, "Без бренду", 1,
        )
        assert len(result) == 0

    def test_invalid_category_skipped(self):
        result = validate_and_sanitize_offers(
            [make_offer(category_id=9999)], VALID_CATEGORIES, "Без бренду", 1,
        )
        assert len(result) == 0

    def test_missing_stock_quantity_gets_default(self):
        result = validate_and_sanitize_offers(
            [make_offer(stock_quantity="")], VALID_CATEGORIES, "Без бренду", 5,
        )
        assert result[0]["field_mappings"]["stock_quantity"] == "5"

    def test_missing_vendor_gets_default(self):
        result = validate_and_sanitize_offers(
            [make_offer(vendor="", name="Ніж мисливський")], VALID_CATEGORIES, "Без бренду", 1,
        )
        assert result[0]["field_mappings"]["vendor"] == "Без бренду"
        assert "Без бренду" in result[0]["field_mappings"]["name"]

    def test_duplicate_names_logged(self, caplog):
        offers = [
            make_offer(offer_id="id-1", name="Ніж Prosta Stal"),
            make_offer(offer_id="id-2", name="Ніж Prosta Stal"),
        ]
        with caplog.at_level("WARNING"):
            result = validate_and_sanitize_offers(offers, VALID_CATEGORIES, "Без бренду", 1)
        assert len(result) == 2
        assert "duplicate name" in caplog.text.lower()

    def test_missing_article_warns(self, caplog):
        with caplog.at_level("WARNING"):
            validate_and_sanitize_offers(
                [make_offer(article="")], VALID_CATEGORIES, "Без бренду", 1,
            )
        assert "article" in caplog.text.lower()

    def test_missing_params_warns(self, caplog):
        with caplog.at_level("WARNING"):
            validate_and_sanitize_offers(
                [make_offer(params=[])], VALID_CATEGORIES, "Без бренду", 1,
            )
        assert "no params" in caplog.text.lower()

    def test_description_sanitized(self):
        result = validate_and_sanitize_offers(
            [make_offer(description="Чудовий ніж https://example.com зв'яжіться з нами 📞")],
            VALID_CATEGORIES, "Без бренду", 1,
        )
        desc = result[0]["field_mappings"]["description"]
        assert "https://example.com" not in desc
        assert "📞" not in desc

    def test_name_template_applied(self):
        result = validate_and_sanitize_offers(
            [make_offer(name="original Prosta Stal", vendor="Prosta Stal", model="Корольов", article="PSK-001")],
            VALID_CATEGORIES, "Без бренду", 1,
            name_template="{name} {vendor} {model} {article}",
        )
        name = result[0]["field_mappings"]["name"]
        assert "Prosta Stal" in name
        assert "Корольов" in name

    def test_multiple_offers_mixed(self):
        offers = [
            make_offer(offer_id="good", name="Ніж Prosta Stal", price="100"),
            make_offer(offer_id="no-price", name="Ніж 2 Prosta Stal", price=""),
            make_offer(offer_id="bad-cat", name="Ніж 3 Prosta Stal", category_id=9999),
            make_offer(offer_id="good-2", name="Сокира Prosta Stal", price="200"),
        ]
        result = validate_and_sanitize_offers(offers, VALID_CATEGORIES, "Без бренду", 1)
        assert {r["id"] for r in result} == {"good", "good-2"}
