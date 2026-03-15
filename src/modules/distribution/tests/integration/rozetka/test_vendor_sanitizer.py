"""Tests for VendorSanitizer."""
from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_vendor_sanitizer import VendorSanitizer


class TestVendorSanitizer:
    def test_strips_tm(self):
        assert VendorSanitizer.clean("ТМ Prosta Stal") == "Prosta Stal"

    def test_strips_tov(self):
        assert VendorSanitizer.clean("ТОВ Ковалі") == "Ковалі"

    def test_strips_fop(self):
        assert VendorSanitizer.clean("ФОП Іванов") == "Іванов"

    def test_strips_ltd(self):
        assert VendorSanitizer.clean("ЛТД Knives") == "Knives"

    def test_strips_торгова_марка(self):
        result = VendorSanitizer.clean("торгова марка SteelPro")
        assert "торгова марка" not in result
        assert "SteelPro" in result

    def test_fixes_all_caps(self):
        assert VendorSanitizer.clean("PROSTA STAL") == "Prosta Stal"

    def test_keeps_short_caps(self):
        assert VendorSanitizer.clean("PSK") == "PSK"

    def test_normal_vendor_unchanged(self):
        assert VendorSanitizer.clean("Prosta Stal") == "Prosta Stal"

    def test_empty_string(self):
        assert VendorSanitizer.clean("") == ""
