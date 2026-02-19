"""Module containing all project enums."""
from enum import StrEnum

class SheathColor(StrEnum):
    """Available colors for sheaths."""
    BLACK = "Чорний"
    COLOR = "Кольоровий"
    CAMO = "Камуфляж"
    SKELETON = "Скелетник"

class MountType(StrEnum):
    """Types of knife mounts."""
    MOLLE_LOK = "MolleLok"
    TEK_LOK = "TekLok"
    FREE_SUSPENSION = "Вільний підвіс"
    CLIP = "Кліпса"
    THIGH_MOUNT = "Кріплення на стегно"
    MOLLY_PLATFORM = "Платформа Моллі"

class Status(StrEnum):
    """Item processing status."""
    PENDING = "Pending"
    PROCESSED = "Processed"
