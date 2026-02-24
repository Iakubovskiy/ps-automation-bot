"""Module containing all project enums."""
from enum import StrEnum

class SheathColor(StrEnum):
    """Available colors for sheaths."""
    BLACK = "Чорні"
    COLOR = "Кольорові"
    CAMO = "Комуфляж"
    SKELETON = "Піхви скелетник"

class MountType(StrEnum):
    """Types of knife mounts."""
    NONE = "Без кріплення"
    MOLLE_LOK = "Моллі-Лок"
    TEK_LOK = "Тек-Лок"
    FREE_SUSPENSION = "Вільний підвіс"
    CLIP = "U-кліпса"
    THIGH_MOUNT = "Стегно Тек-лок"
    MOLLY_PLATFORM = " Стегно Моллі-Лок"
