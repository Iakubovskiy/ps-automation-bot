"""Use case: Create a new User within an Organization."""
import logging

from modules.users.application.user.create.dto.create_user_dto import CreateUserDto
from modules.users.domain.events.user_created import UserCreatedEvent
from modules.users.domain.organization import Organization
from modules.users.domain.role import Role
from modules.users.domain.user import User

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    """Creates a new User, assigns a Role, and publishes UserCreatedEvent.

    This is an internal event — it does NOT go through the shared EventBus.
    Other modules do not consume this event.
    """

    def execute(self, dto: CreateUserDto) -> User:
        """Create and return a new User.

        Args:
            dto: Validated input data for user creation.

        Returns:
            The newly created User instance.

        Raises:
            Organization.DoesNotExist: If the organization_id is invalid.
            Role.DoesNotExist: If no role with the given code exists.
            django.db.IntegrityError: If email or telegram_id is not unique.
        """
        organization = Organization.objects.get(pk=dto.organization_id)
        role = Role.objects.get(code=dto.role_code)

        user = User(
            organization=organization,
            email=dto.email,
            role=role,
            telegram_id=dto.telegram_id,
        )
        user.set_password(dto.password)
        user.save()

        logger.info(
            "Created user %s (org=%s, role=%s)",
            user.email,
            organization.name,
            role.code,
        )

        # Internal event — stays within Users module
        event = UserCreatedEvent(
            user_id=str(user.id),
            organization_id=str(organization.id),
            email=user.email,
            role_code=role.code,
        )
        logger.debug("UserCreatedEvent: %s", event)

        return user
