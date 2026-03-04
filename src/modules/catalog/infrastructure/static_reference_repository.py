"""Repository for StaticReference and StaticReferenceGroup queries."""
from modules.catalog.domain.static_reference import StaticReference
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


class StaticReferenceGroupRepository:
    """Query interface for StaticReferenceGroup entities."""

    @staticmethod
    def find_by_organization(organization_id: str) -> list[StaticReferenceGroup]:
        """Return all groups for an organization."""
        return list(
            StaticReferenceGroup.objects.filter(
                organization_id=organization_id,
            ).order_by("name")
        )

    @staticmethod
    def find_by_name(organization_id: str, name: str) -> StaticReferenceGroup | None:
        """Look up a group by name within an organization."""
        return StaticReferenceGroup.objects.filter(
            organization_id=organization_id,
            name=name,
        ).first()


class StaticReferenceRepository:
    """Query interface for StaticReference entities."""

    @staticmethod
    def find_by_group(organization_id: str, group_name: str) -> list[StaticReference]:
        """Return all items in a group for an organization.

        Used by the bot to build inline keyboards for STATIC_DB attributes.
        """
        return list(
            StaticReference.objects.filter(
                group__organization_id=organization_id,
                group__name=group_name,
            ).order_by("label")
        )

    @staticmethod
    def find_by_key(organization_id: str, group_name: str, key: str) -> StaticReference | None:
        """Look up a single reference item by its key within a group."""
        return StaticReference.objects.filter(
            group__organization_id=organization_id,
            group__name=group_name,
            key=key,
        ).first()

    @staticmethod
    def find_by_group_id(group_id: str) -> list[StaticReference]:
        """Return all items in a group by group UUID."""
        return list(
            StaticReference.objects.filter(
                group_id=group_id,
            ).order_by("label")
        )
