"""Public portfolio summaries use only the ancestry frozen for each stay."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.properties.models import (
    ResidentialBuilding,
    ResidentialComplex,
    Property,
)
from .visibility import sections, visible, summarize_rows


def rows(kind, identity):
    if kind not in {"building", "complex"}:
        raise NotFound()
    return [
        section
        for section in sections()
        .filter(
            subject_kind="property_stay",
            content_state="approved",
            **{
                f"submission__opportunity__case__source_snapshot__{kind}_id": str(
                    identity
                )
            },
        )
        .order_by("-created_at", "-id")
        if section.verification_basis != "legacy_unverified"
        and visible(section, public_only=True)
    ]


def summary(kind, identity):
    model = (
        ResidentialBuilding
        if kind == "building"
        else ResidentialComplex if kind == "complex" else None
    )
    if not model:
        raise NotFound()
    container = get_object_or_404(model, id=identity)
    items = rows(kind, identity)
    # No authority documents, contacts, or private portfolio fields are returned.
    return {
        **summarize_rows("property_stay", items),
        "portfolio_kind": kind,
        "portfolio_id": str(identity),
        "name": container.name,
        "archived": container.archived,
        "distinct_unit_count": len({x.subject_id for x in items}),
        "ancestry_basis": "recorded_at_occupancy",
    }


def property_links(identity):
    prop = get_object_or_404(Property, id=identity)
    if prop.status != "verified" or prop.retired_at:
        raise NotFound()
    from .ancestry import from_property

    current = from_property(prop)
    snapshots = [current] + [
        s.submission.opportunity.case.source_snapshot
        for s in sections().filter(subject_kind="property_stay", subject_id=identity)
        if visible(s, public_only=True)
    ]
    found = {}
    for snap in snapshots:
        for kind in ("building", "complex"):
            key = snap.get(f"{kind}_id")
            if key:
                found[(kind, key)] = {
                    "id": key,
                    "kind": kind,
                    "name": snap.get(f"{kind}_name") or "",
                    "historical": current.get(f"{kind}_id") != key,
                }
    return list(found.values())
