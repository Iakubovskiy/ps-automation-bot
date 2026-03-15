"""Tests for DescriptionSanitizer."""
from redis.commands.search.querystring import equal

from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_description_sanitizer import DescriptionSanitizer


class TestDescriptionSanitizer:
    def test_removes_urls(self):
        result = DescriptionSanitizer.sanitize(
            "Опис товару https://example.com і ще текст", "id-1",
        )
        assert "https://example.com" not in result
        assert "ще текст" in result
        assert "Опис товару і ще текст" == result

    def test_removes_www_urls(self):
        result = DescriptionSanitizer.sanitize("Опис www.example.com кінець", "id-1")
        assert "www.example.com" not in result

    def test_removes_emails(self):
        result = DescriptionSanitizer.sanitize(
            "Пишіть на info@shop.com для замовлень", "id-1",
        )
        assert "info@shop.com" not in result

    def test_removes_emoji(self):
        result = DescriptionSanitizer.sanitize("Чудовий ніж 🔥🗡️✨", "id-1")
        assert "🔥" not in result
        assert "🗡" not in result
        assert "✨" not in result
        assert "ніж" in result

    def test_removes_stop_phrases_tov(self):
        result = DescriptionSanitizer.sanitize("Виробник ТОВ Ковалі якісно", "id-1")
        assert "ТОВ " not in result

    def test_removes_stop_phrases_delivery(self):
        result = DescriptionSanitizer.sanitize(
            "Хороший товар. Безкоштовна доставка по Україні", "id-1",
        )
        assert "безкоштовна доставка" not in result.lower()

    def test_removes_contact_us(self):
        result = DescriptionSanitizer.sanitize(
            "Виготовимо протягом тижня. Для деталей зв'яжіться з нами телефоном", "id-1",
        )
        assert "Для деталей зв'яжіться з нами телефоном" not in result

    def test_preserves_normal_text(self):
        normal = "Мисливський ніж з клинком зі сталі 95Х18. Загальна довжина 250мм."
        result = DescriptionSanitizer.sanitize(normal, "id-1")
        assert result == normal

    def test_collapses_whitespace(self):
        result = DescriptionSanitizer.sanitize("Текст     з     пробілами", "id-1")
        assert "     " not in result
