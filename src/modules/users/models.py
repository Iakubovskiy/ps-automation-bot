"""Re-export domain models so Django can discover them for migrations."""
from modules.users.domain.organization import Organization  # noqa: F401
from modules.users.domain.role import Role  # noqa: F401
from modules.users.domain.user import User  # noqa: F401
