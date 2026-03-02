"""DTO for creating a new User."""
from pydantic import BaseModel, EmailStr


class CreateUserDto(BaseModel):
    """Data required to create a new User within an Organization.

    Attributes:
        organization_id: UUID of the Organization the user belongs to.
        email: Unique email address.
        password: Raw password (will be hashed by the domain model).
        role_code: One of OWNER, ADMIN, MANAGER.
        telegram_id: Optional Telegram user ID for bot integration.
    """

    organization_id: str
    email: EmailStr
    password: str
    role_code: str = "MANAGER"
    telegram_id: int | None = None
