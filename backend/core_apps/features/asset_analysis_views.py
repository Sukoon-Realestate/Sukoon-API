from django.http import Http404
from config.advanced_housing import manual_review_available, mock_mode_available
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from .asset_passport_models import (
    AssetItem,
    AssetAnalysisJob,
    AssetPatternCase,
    AssetSharedSystem,
    AssetWarrantyReference,
)
from .services.planning import planning_api, mutate, require_planning
from .services.asset_passport import access, analysis, investigations, evidence


def gated(request):
    require_planning(request.user, "asset_assisted_analysis")


@planning_api(["GET"], None)
def workspace(request, asset_id):
    asset = access.asset_for(request.user, asset_id)
    observations = [
        evidence.observation_payload(row, request.user)
        for row in asset.observations.select_related(
            "asset", "property", "lease", "author"
        ).order_by("-observed_on")
        if evidence.visible_observation(row, request.user)
    ]
    jobs, systems, cases, warranties = [], [], [], []
    for row in asset.analysis_jobs.order_by("-created_at")[:30]:
        try:
            jobs.append(
                analysis.payload(analysis.job_for(request.user, row.id), request.user)
            )
        except (NotFound, Http404):
            pass
    for row in asset.shared_systems.all():
        try:
            systems.append(
                investigations.system_payload(
                    investigations.system_for(request.user, row.id)
                )
            )
            for case in row.cases.order_by("-created_at")[:20]:
                try:
                    cases.append(
                        investigations.case_payload(
                            investigations.case_for(request.user, case.id)
                        )
                    )
                except (NotFound, Http404):
                    pass
        except (NotFound, Http404):
            pass
    for row in asset.warranty_references.all():
        try:
            warranties.append(
                investigations.warranty_payload(
                    investigations.warranty_for(request.user, row.id)
                )
            )
        except (NotFound, Http404):
            pass
    siblings = []
    if (
        asset.property.building_id
        and asset.property.building.manager_id == request.user.pk
    ):
        for row in AssetItem.objects.filter(
            property__building=asset.property.building, property__owner=request.user
        ).select_related("property")[:100]:
            siblings.append(
                {
                    "id": str(row.id),
                    "label": row.label,
                    "property_id": str(row.property.id),
                    "observations": [
                        {
                            "id": str(obs.id),
                            "condition": obs.condition,
                            "observed_on": str(obs.observed_on),
                        }
                        for obs in row.observations.all()
                        if evidence.visible_observation(obs, request.user)
                    ],
                }
            )
    return Response(
        {
            "analysis_mode": (
                "manual"
                if manual_review_available()
                else "mock" if mock_mode_available() else "disabled"
            ),
            "id": str(asset.id),
            "revision": asset.revision,
            "label": asset.label,
            "property_id": str(asset.property.id),
            "building_id": str(asset.property.building.id) if siblings else "",
            "observations": observations,
            "jobs": jobs,
            "systems": systems,
            "cases": cases,
            "warranties": warranties,
            "system_candidates": siblings,
            "allowed_actions": access.actions(
                request.user, "asset_assisted_analysis", str(asset.id)
            ),
        }
    )


@planning_api(["POST"], None)
def create_analysis(request, asset_id):
    gated(request)
    return mutate(
        request,
        "asset.analyze",
        lambda: access.asset_for(request.user, asset_id, lock=True),
        lambda item, _: analysis.create(request.user, item, request.data),
        lambda job: analysis.payload(job, request.user),
    )


@planning_api(["GET", "POST"], None)
def job_detail(request, record_id):
    if request.method == "GET":
        return Response(
            analysis.payload(analysis.job_for(request.user, record_id), request.user)
        )
    gated(request)
    return mutate(
        request,
        "asset.analysis_cancel",
        lambda: analysis.job_for(request.user, record_id, lock=True),
        lambda job, _: analysis.cancel(request.user, job),
        lambda job: analysis.payload(job, request.user),
    )


@planning_api(["POST"], None)
def review_finding(request, record_id):
    # Preserve authorized review of an existing manual case after creation is disabled.
    return mutate(
        request,
        "asset.finding_review",
        lambda: analysis.finding_for(request.user, record_id, lock=True),
        lambda row, _: analysis.review(request.user, row, request.data),
        analysis.finding_payload,
    )


@planning_api(["POST"], None)
def create_system(request, asset_id):
    gated(request)
    return mutate(
        request,
        "asset.shared_system",
        lambda: access.asset_for(request.user, asset_id, write=True, lock=True),
        lambda row, _: investigations.create_system(request.user, row, request.data),
        investigations.system_payload,
    )


@planning_api(["POST"], None)
def open_case(request, record_id):
    gated(request)
    return mutate(
        request,
        "asset.pattern_open",
        lambda: investigations.system_for(request.user, record_id, lock=True),
        lambda row, _: investigations.create_case(request.user, row, request.data),
        investigations.case_payload,
    )


@planning_api(["POST"], None)
def close_case(request, record_id):
    gated(request)
    return mutate(
        request,
        "asset.pattern_close",
        lambda: investigations.case_for(request.user, record_id, lock=True),
        lambda row, _: investigations.close_case(request.user, row, request.data),
        investigations.case_payload,
    )


@planning_api(["POST"], None)
def create_warranty(request, asset_id):
    gated(request)
    return mutate(
        request,
        "asset.warranty_record",
        lambda: access.asset_for(request.user, asset_id, write=True, lock=True),
        lambda row, _: investigations.warranty(request.user, row, request.data),
        investigations.warranty_payload,
    )


@planning_api(["POST"], None)
def claim_warranty(request, record_id):
    gated(request)
    return mutate(
        request,
        "asset.warranty_claim",
        lambda: investigations.warranty_for(request.user, record_id, lock=True),
        lambda row, _: investigations.claim(request.user, row, request.data),
        investigations.warranty_payload,
    )
