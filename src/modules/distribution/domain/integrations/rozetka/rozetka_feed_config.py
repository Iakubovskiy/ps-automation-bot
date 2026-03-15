"""RozetkaFeedConfig domain entity.

One-to-one configuration for a Rozetka XML feed driver.
"""
import secrets

from django.db import models


class RozetkaFeedConfig(models.Model):
    """Configuration for a Rozetka XML feed linked to a DistributionDriver."""

    driver = models.OneToOneField(
        "distribution.DistributionDriver",
        on_delete=models.CASCADE,
        related_name="rozetka_feed_config",
    )
    feed_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Auto-generated token used in the feed URL for security",
    )
    shop_name = models.CharField(
        max_length=255,
        help_text="Shop name for <name> tag in XML feed",
    )
    shop_url = models.URLField(
        blank=True,
        default="",
        help_text="Shop URL for <url> tag in XML feed",
    )
    CURRENCY_CHOICES = [
        ("UAH", "UAH (гривня)"),
        ("USD", "USD (долар)"),
        ("EUR", "EUR (євро)"),
    ]
    currency = models.CharField(
        max_length=3,
        default="UAH",
        choices=CURRENCY_CHOICES,
        help_text="Default currency for offers (rate=1). Rozetka supports UAH, USD, EUR.",
    )
    media_base_url = models.URLField(
        help_text="Base URL prepended to S3 keys for public image URLs",
    )
    default_vendor = models.CharField(
        max_length=255,
        blank=True,
        default="Без бренду",
        help_text="Default vendor when product has no vendor mapped (Rozetka requires this)",
    )
    default_stock_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Default stock_quantity when not mapped on a product (0 = out of stock)",
    )
    name_template = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text=(
            "Template for building <name>. Uses {field} placeholders from mapped attributes. "
            "Special: {vendor}, {article}, {param:Назва параметру}. "
            "Example: {product_type} {vendor} {model} {param:Довжина клинка} мм {article}"
        ),
    )
    rozetka_name_instructions = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Extra AI prompt instructions for generating Rozetka-compliant product names. "
            "Appended to system_prompt when generating AI content. "
            "E.g.: 'Generate rozetka_name field following Rozetka naming rules...'"
        ),
    )
    rozetka_description_instructions = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Extra AI prompt instructions for generating Rozetka-compliant descriptions. "
            "E.g.: 'Generate rozetka_description without URLs, phones, emoji...'"
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "distribution_rozetka_feed_config"
        verbose_name = "Rozetka Feed Config"
        verbose_name_plural = "Rozetka Feed Configs"

    def __str__(self) -> str:
        return f"Rozetka Feed: {self.shop_name}"

    def save(self, *args, **kwargs):
        if not self.feed_token:
            self.feed_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
