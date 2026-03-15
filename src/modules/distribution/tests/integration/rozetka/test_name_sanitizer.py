"""Tests for NameSanitizer."""
from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_name_sanitizer import NameSanitizer


class TestSanitizeName:
    def test_removes_quotes(self):
        result = NameSanitizer.sanitize('Ніж "Корольов" сталевий', "Prosta Stal")
        assert '"' not in result

    def test_removes_brackets(self):
        result = NameSanitizer.sanitize("Ніж (полімер чорний)", "Prosta Stal")
        assert "(" not in result
        assert ")" not in result

    def test_removes_guillemets(self):
        result = NameSanitizer.sanitize("Ніж «Корольов»", "Prosta Stal")
        assert "«" not in result
        assert "»" not in result

    def test_appends_vendor_if_missing(self):
        result = NameSanitizer.sanitize("Ніж мисливський Корольов", "Prosta Stal")
        assert "Prosta Stal" in result

    def test_inserts_vendor_after_first_word(self):
        result = NameSanitizer.sanitize("Ніж мисливський", "Prosta Stal")
        assert result == "Ніж Prosta Stal мисливський"

    def test_keeps_vendor_if_present(self):
        result = NameSanitizer.sanitize("Ніж Prosta Stal мисливський", "Prosta Stal")
        assert result.count("Prosta Stal") == 1

    def test_vendor_case_insensitive_check(self):
        result = NameSanitizer.sanitize("Ніж prosta stal мисливський", "Prosta Stal")
        assert result.count("rosta") == 1

    def test_collapses_spaces(self):
        result = NameSanitizer.sanitize("Ніж   мисливський   Prosta Stal", "Prosta Stal")
        assert "  " not in result

    def test_empty_vendor_no_append(self):
        result = NameSanitizer.sanitize("Ніж мисливський", "")
        assert result == "Ніж мисливський"


class TestBuildNameFromTemplate:
    def test_simple_template(self):
        result = NameSanitizer.build_from_template(
            "{name} {vendor}",
            {"name": "Ніж мисливський", "vendor": "Prosta Stal"}, [], "id-1",
        )
        assert result == "Ніж мисливський Prosta Stal"

    def test_full_template(self):
        result = NameSanitizer.build_from_template(
            "{name} {vendor} {model} {article}",
            {"name": "Ніж", "vendor": "Prosta Stal", "model": "Корольов", "article": "PSK-001"},
            [], "id-1",
        )
        assert result == "Ніж Prosta Stal Корольов PSK-001"

    def test_param_placeholder(self):
        result = NameSanitizer.build_from_template(
            "{name} {vendor} {param:Довжина клинка} мм",
            {"name": "Ніж", "vendor": "Prosta Stal"},
            [("Довжина клинка", "120")], "id-1",
        )
        assert result == "Ніж Prosta Stal 120 мм"

    def test_missing_field_omitted(self):
        result = NameSanitizer.build_from_template(
            "{name} {vendor} {model}",
            {"name": "Ніж", "vendor": "Prosta Stal"}, [], "id-1",
        )
        assert result == "Ніж Prosta Stal"

    def test_missing_param_omitted(self):
        result = NameSanitizer.build_from_template(
            "{name} {param:Колір}", {"name": "Ніж"}, [], "id-1",
        )
        assert result == "Ніж"

    def test_all_missing_returns_none(self):
        result = NameSanitizer.build_from_template(
            "{nonexistent} {param:Немає}", {}, [], "id-1",
        )
        assert result is None

    def test_list_param_joined(self):
        result = NameSanitizer.build_from_template(
            "{name} {param:Матеріал}", {"name": "Ніж"},
            [("Матеріал", ["дерево", "шкіра"])], "id-1",
        )
        assert "дерево, шкіра" in result

    def test_static_text_preserved(self):
        result = NameSanitizer.build_from_template(
            "Ніж мисливський {vendor} — модель {model}",
            {"vendor": "Prosta Stal", "model": "Танто"}, [], "id-1",
        )
        assert result == "Ніж мисливський Prosta Stal — модель Танто"

    def test_trailing_separators_stripped(self):
        result = NameSanitizer.build_from_template(
            "{name} {vendor} -",
            {"name": "Ніж", "vendor": "Prosta Stal"}, [], "id-1",
        )
        assert not result.endswith("-")
        assert not result.endswith(" ")
