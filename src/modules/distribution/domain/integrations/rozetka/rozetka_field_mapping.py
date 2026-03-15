"""RozetkaFieldMapping — maps product attributes to Rozetka XML fields."""
from django.db import models


class RozetkaField(models.TextChoices):
    """Target XML fields for Rozetka YML feed (per-offer)."""

    # Product title
    NAME = "name", "name (product title)"
    NAME_UA = "name_ua", "name_ua (Ukrainian title)"
    DESCRIPTION = "description", "description (HTML in CDATA)"
    DESCRIPTION_UA = "description_ua", "description_ua (HTML in CDATA)"
    VENDOR = "vendor", "vendor (brand)"
    PRICE = "price", "price"
    PRICE_OLD = "price_old", "price_old (strikethrough)"
    PRICE_PROMO = "price_promo", "price_promo (promo page)"
    CURRENCY_ID = "currencyId", "currencyId (UAH/USD/EUR per offer)"
    # Inventory
    STOCK_QUANTITY = "stock_quantity", "stock_quantity"
    # Identifiers
    ARTICLE = "article", "article (vendorCode / SKU)"
    MODEL = "model", "model"
    URL = "url", "url (product page link)"
    STATE = "state", "state (new/used/refurbished/stock)"
    DOCKET = "docket", "docket (short desc, required for used/stock)"
    DOCKET_UA = "docket_ua", "docket_ua"
    PICTURE = "picture", "picture (photo field)"
    # Per-product Rozetka category override (value must be a declared rz_id)
    CATEGORY_ID = "rozetka_category_id", "rozetka_category_id (per-product override)"
    PARAM = "param", "param (custom parameter)"

class RozetkaFieldMapping(models.Model):
    """Maps a product attribute key to a Rozetka XML field for a given driver+schema."""

    feed_config = models.ForeignKey(
        "distribution.RozetkaFeedConfig",
        on_delete=models.CASCADE,
        related_name="field_mappings",
    )
    product_schema = models.ForeignKey(
        "catalog.ProductSchema",
        on_delete=models.CASCADE,
        related_name="rozetka_field_mappings",
    )
    attribute_key = models.CharField(
        max_length=128,
        help_text="Key in product.attributes to read the value from",
    )
    rozetka_field = models.CharField(
        max_length=64,
        choices=RozetkaField.choices,
        help_text="Target XML field in the Rozetka feed",
    )
    param_name = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text='<param name="..."> when rozetka_field is PARAM',
    )

    class Meta:
        db_table = "distribution_rozetka_field_mapping"
        verbose_name = "Rozetka Field Mapping"
        verbose_name_plural = "Rozetka Field Mappings"
        unique_together = [("feed_config", "product_schema", "attribute_key")]

    def __str__(self) -> str:
        target = self.param_name if self.rozetka_field == RozetkaField.PARAM else self.rozetka_field
        return f"{self.attribute_key} → {target}"
