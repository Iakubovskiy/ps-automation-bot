"""Repository for StaticReference queries.

Wraps Django ORM to provide a clean interface for the application layer.
"""
from modules.catalog.domain.static_reference import StaticReference


class StaticReferenceRepository:
    """Query interface for StaticReference entities."""

    @staticmethod
    def find_by_group(organization_id: str, group_name: str) -> list[StaticReference]:
        """Return all references in a group for an organization.

        Used by the bot to build inline keyboards for STATIC_DB attributes.
        """
        return list(
            StaticReference.objects.filter(
                organization_id=organization_id,
                group_name=group_name,
            ).order_by("label")
        )

    @staticmethod
    def find_by_key(organization_id: str, group_name: str, key: str) -> StaticReference | None:
        """Look up a single reference by its key within a group."""
        return StaticReference.objects.filter(
            organization_id=organization_id,
            group_name=group_name,
            key=key,
        ).first()

    @staticmethod
    def get_group_names(organization_id: str) -> list[str]:
        """Return distinct group names for an organization."""
        return list(
            StaticReference.objects.filter(
                organization_id=organization_id,
            ).values_list("group_name", flat=True).distinct().order_by("group_name")
        )
