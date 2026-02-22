"""DTO for product data collected from Telegram and Google Sheets."""
from dataclasses import dataclass, field


@dataclass
class InputProductData:
    """Input product data that the ProductManager accepts for processing.

    Combines data collected via Telegram bot and looked up from Google Sheets.
    """

    blade_name: str
    total_length: int
    blade_length: int
    blade_width: int
    blade_weight: int
    blade_thickness: int
    hardness: int
    sharpening_angle: int
    configuration_type: str | None
    blade_type: str
    sheath_type: str
    attachments: list[str] = field(default_factory=list)
    has_honing_rod: bool = False
    has_lanyard: bool = False
    has_flint: bool = False
    engraving_count: int = 0
    handle_type: str | None = None
    steel: str = ""
    price: float = 0.0
    photos: list[str] = field(default_factory=list)
