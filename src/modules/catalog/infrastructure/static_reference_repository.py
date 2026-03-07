"""Repository for StaticReference and StaticReferenceGroup queries.

Provides both sync and async interfaces.
"""
from modules.catalog.domain.static_reference import StaticReference
from modules.catalog.domain.static_reference_group import StaticReferenceGroup


class StaticReferenceGroupRepository:
    """Query interface for StaticReferenceGroup entities."""

    @staticmethod
    def find_by_organization(organization_id: str) -> list[StaticReferenceGroup]:
        return list(
            StaticReferenceGroup.objects.filter(
                organization_id=organization_id,
            ).order_by("name")
        )

    @staticmethod
    async def afind_by_organization(organization_id: str) -> list[StaticReferenceGroup]:
        return [
            g async for g in
            StaticReferenceGroup.objects.filter(
                organization_id=organization_id,
            ).order_by("name")
        ]

    @staticmethod
    def find_by_name(organization_id: str, name: str) -> StaticReferenceGroup | None:
        return StaticReferenceGroup.objects.filter(
            organization_id=organization_id, name=name,
        ).first()

    @staticmethod
    async def afind_by_name(organization_id: str, name: str) -> StaticReferenceGroup | None:
        return await StaticReferenceGroup.objects.filter(
            organization_id=organization_id, name=name,
        ).afirst()


class StaticReferenceRepository:
    """Query interface for StaticReference entities."""

    @staticmethod
    def find_by_group(organization_id: str, group_name: str) -> list[StaticReference]:
        return list(
            StaticReference.objects.filter(
                group__organization_id=organization_id,
                group__name=group_name,
            ).order_by("label")
        )

    @staticmethod
    async def afind_by_group(organization_id: str, group_name: str) -> list[StaticReference]:
        return [
            r async for r in
            StaticReference.objects.filter(
                group__organization_id=organization_id,
                group__name=group_name,
            ).order_by("label")
        ]

    @staticmethod
    def find_by_key(organization_id: str, group_name: str, key: str) -> StaticReference | None:
        return StaticReference.objects.filter(
            group__organization_id=organization_id,
            group__name=group_name,
            key=key,
        ).first()

    @staticmethod
    async def afind_by_key(organization_id: str, group_name: str, key: str) -> StaticReference | None:
        return await StaticReference.objects.filter(
            group__organization_id=organization_id,
            group__name=group_name,
            key=key,
        ).afirst()

    @staticmethod
    def find_by_group_id(group_id: str) -> list[StaticReference]:
        return list(
            StaticReference.objects.filter(group_id=group_id).order_by("label")
        )

    @staticmethod
    async def afind_by_group_id(group_id: str) -> list[StaticReference]:
        return [
            r async for r in
            StaticReference.objects.filter(group_id=group_id).order_by("label")
        ]
