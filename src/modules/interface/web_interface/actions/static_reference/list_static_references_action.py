"""Action: List static references for an organization."""
from ninja import Router, Schema
from typing import Any

from modules.catalog.infrastructure.static_reference_repository import StaticReferenceRepository

router = Router()


class StaticReferenceSchema(Schema):
    """Response schema for a static reference."""

    id: str
    group_name: str
    key: str
    label: str
    value: dict[str, Any]


@router.get("/static-references", response=list[StaticReferenceSchema], tags=["Static References"])
def list_static_references(request, organization_id: str, group_name: str = None):
    """List static references for an organization, optionally filtered by group."""
    if group_name:
        refs = StaticReferenceRepository.find_by_group(organization_id, group_name)
    else:
        # Return all — need a custom query since repository doesn't have find_all_by_org
        from modules.catalog.domain.static_reference import StaticReference
        refs = StaticReference.objects.filter(
            organization_id=organization_id,
        ).order_by("group_name", "label")

    return [
        StaticReferenceSchema(
            id=str(r.id),
            group_name=r.group_name,
            key=r.key,
            label=r.label,
            value=r.value,
        )
        for r in refs
    ]
