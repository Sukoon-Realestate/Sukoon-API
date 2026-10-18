"""Source-bound mock comparison. Metadata rules do not inspect pixels or assign blame."""

from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from config.advanced_housing import require_mock_mode, manual_review_available
from ...asset_passport_models import (
    AssetObservation,
    AssetAnalysisJob,
    AssetAnalysisSuggestion,
)
from ..planning import text_field
from ..rental_lifecycle.common import audit
from ..rental_phase2 import fingerprint, RentalConflict
from . import access, evidence

VERSION = "asset-review-v2"
CAPTURE_QUALITY = {
    "unknown",
    "comparable",
    "low_light",
    "different_angle",
    "obstructed",
    "identity_uncertain",
}


def capture_context(data):
    value = data.get("capture_context", {})
    if not isinstance(value, dict) or set(value) - {
        "quality",
        "reported_capture_at",
        "identity_confirmed",
    }:
        raise ValidationError(
            {"capture_context": "Supply a supported reported capture context."}
        )
    quality = value.get("quality", "unknown")
    if (
        quality not in CAPTURE_QUALITY
        or type(value.get("identity_confirmed", False)) is not bool
    ):
        raise ValidationError(
            {
                "capture_context": "Choose a reported quality and confirm the physical item explicitly."
            }
        )
    reported = value.get("reported_capture_at", "")
    if not isinstance(reported, str) or len(reported) > 60:
        raise ValidationError(
            {"capture_context": "Supply a bounded reported capture timestamp."}
        )
    return {
        "quality": quality,
        "identity_confirmed": value.get("identity_confirmed", False),
        "reported_capture_at": reported,
        "independently_verified": False,
    }


def manifest(user, observations):
    result = []
    for row in observations:
        if not evidence.visible_observation(row, user):
            raise NotFound()
        source = evidence.source_for(user, row.source_kind, row.source_id)
        selected = list(
            evidence.safe_evidence(source).filter(id__in=row.evidence.values("id"))
        )
        result.append(
            {
                "observation_id": str(row.id),
                "asset_id": str(row.asset.id),
                "property_id": str(row.property.id),
                "observed_on": str(row.observed_on),
                "condition": row.condition,
                "source_kind": row.source_kind,
                "source_id": str(row.source_id),
                "source_revision": source.revision,
                "source_status": source.status,
                "capture_context": row.capture_context,
                "server_received_at": row.created_at.isoformat(),
                "evidence": [
                    {
                        "id": str(media.id),
                        "sha256": media.sha256,
                        "content_type": media.content_type,
                        "server_received_at": media.created_at.isoformat(),
                    }
                    for media in sorted(selected, key=lambda media: str(media.id))
                ],
            }
        )
    return sorted(result, key=lambda row: (row["observed_on"], row["observation_id"]))


def observations_for(user, ids, *, asset=None):
    if (
        not isinstance(ids, list)
        or not 2 <= len(ids) <= 8
        or any(not isinstance(v, str) for v in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValidationError(
            {"observation_ids": "Choose two to eight distinct authorized observations."}
        )
    query = AssetObservation.objects.filter(id__in=ids).select_related(
        "asset", "property", "lease"
    )
    if asset:
        query = query.filter(asset=asset)
    rows = list(query)
    if len(rows) != len(ids):
        raise NotFound()
    manifest(user, rows)
    return rows


def job_for(user, identifier, *, lock=False):
    query = AssetAnalysisJob.objects.select_related("asset", "created_by")
    if lock:
        query = query.select_for_update(of=("self",))
    job = get_object_or_404(query, id=identifier)
    access.asset_for(user, job.asset.id)
    observations_for(
        user, [row["observation_id"] for row in job.source_manifest], asset=job.asset
    )
    return job


def current_manifest(job, user):
    return manifest(
        user,
        observations_for(
            user,
            [row["observation_id"] for row in job.source_manifest],
            asset=job.asset,
        ),
    )


def create(user, asset, data):
    manual = manual_review_available()
    if not manual:
        require_mock_mode()
    rows = observations_for(user, data.get("observation_ids"), asset=asset)
    original = None
    if data.get("previous_run_id"):
        original = job_for(user, data["previous_run_id"])
        if original.asset_id != asset.pk:
            raise ValidationError(
                {
                    "previous_run_id": "Rerun only an analysis of this same physical item."
                }
            )
    sources = manifest(user, rows)
    job = AssetAnalysisJob.objects.create(
        asset=asset,
        created_by=user,
        previous_run=original,
        source_manifest=sources,
        source_digest=fingerprint(sources),
        provider_version="human-visual-review-v1" if manual else VERSION,
        provider="manual_visual_review" if manual else "mock_asset_rules",
        state="ready_for_review" if manual else "queued",
    )
    audit(job, user, "asset_analysis_queued")
    if manual:
        AssetAnalysisSuggestion.objects.create(
            job=job,
            kind="manual_visual_review",
            uncertainty="unreviewed",
            output={
                "provider": "manual_visual_review",
                "simulated": False,
                "pixels_analyzed_by_model": False,
                "comparison_basis": "awaiting_human_inspection",
                "liability_determined": False,
            },
        )
        return job

    def dispatch():
        try:
            process.delay(str(job.id))
        except Exception:
            AssetAnalysisJob.objects.filter(pk=job.pk, state="queued").update(
                failure_code="worker_dispatch_failed"
            )

    transaction.on_commit(dispatch)
    return job


def mock_compare(sources):
    base = {
        "provider": "mock_asset_rules",
        "model_version": VERSION,
        "simulated": True,
        "comparison_basis": "metadata_and_author_declared_condition_only",
        "source_observation_ids": [row["observation_id"] for row in sources],
        "independent_inspection": False,
        "liability_determined": False,
        "capture_time_verified": False,
    }
    insufficient = any(
        not row["evidence"]
        or row["capture_context"].get("quality") != "comparable"
        or row["capture_context"].get("identity_confirmed") is not True
        for row in sources
    )
    if insufficient:
        return [
            {
                "kind": "insufficient_comparable_evidence",
                "uncertainty": "insufficient",
                "output": {
                    **base,
                    "reason_codes": ["identity_quality_or_coverage_unverified"],
                    "suggested_action": "guided_recapture_or_independent_inspection",
                },
            }
        ]
    hashes = [media["sha256"] for row in sources for media in row["evidence"]]
    result = []
    if len(hashes) != len(set(hashes)):
        result.append(
            {
                "kind": "possible_reused_evidence",
                "uncertainty": "integrity_match_not_capture_proof",
                "output": {
                    **base,
                    "suggested_action": "review_original_capture_context",
                },
            }
        )
    before, after = sources[0], sources[-1]
    result.append(
        {
            "kind": (
                "reported_condition_difference"
                if before["condition"] != after["condition"]
                else "reported_condition_consistency"
            ),
            "uncertainty": "uncalibrated_advisory",
            "output": {
                **base,
                "before_condition": before["condition"],
                "after_condition": after["condition"],
                "observed_difference": "author_labels_only",
                "interpretation": "requires_human_review",
                "suggested_action": "review_sources_and_request_inspection",
            },
        }
    )
    return result


@shared_task(name="advanced_housing.analyze_asset")
def process(identifier):
    from ..planning import enabled_services
    from ..planning_providers import ready_services

    if "asset_assisted_analysis" not in ready_services(enabled_services()):
        return
    with transaction.atomic():
        job = (
            AssetAnalysisJob.objects.select_for_update()
            .select_related("asset", "created_by")
            .get(id=identifier)
        )
        if job.state != "queued" or job.cancellation_requested:
            return
        job.state, job.revision = "processing", job.revision + 1
        claim_revision = job.revision
        job.save()
    try:
        require_mock_mode()
        job_for(job.created_by, identifier)
        if fingerprint(current_manifest(job, job.created_by)) != job.source_digest:
            raise RentalConflict(
                "The evidence snapshot changed. Request a new comparison.",
                code="source_changed",
            )
        outputs = mock_compare(job.source_manifest)
        with transaction.atomic():
            job = AssetAnalysisJob.objects.select_for_update().get(pk=job.pk)
            if (
                job.cancellation_requested
                or job.state != "processing"
                or job.revision != claim_revision
            ):
                return
            if "asset_assisted_analysis" not in ready_services(enabled_services()):
                job.state = "queued"
                job.revision += 1
                job.save()
                return
            if fingerprint(current_manifest(job, job.created_by)) != job.source_digest:
                raise RentalConflict(
                    "The evidence snapshot changed. Request a new comparison.",
                    code="source_changed",
                )
            for output in outputs:
                AssetAnalysisSuggestion.objects.create(job=job, **output)
            job.state = "ready_for_review"
            job.failure_code = ""
            job.completed_at = timezone.now()
            job.revision += 1
            job.save()
    except Exception:
        AssetAnalysisJob.objects.filter(
            pk=job.pk, state="processing", revision=claim_revision
        ).update(
            state="failed",
            failure_code="source_or_provider_unavailable",
            completed_at=timezone.now(),
            revision=claim_revision + 1,
        )


def cancel(user, job):
    if job.created_by_id != user.pk:
        raise NotFound()
    if job.state in {"queued", "processing"}:
        job.cancellation_requested, job.state = True, "cancelled"
        job.revision += 1
        job.save()
    return job


def finding_for(user, identifier, *, lock=False):
    query = AssetAnalysisSuggestion.objects.select_related("job__asset")
    if lock:
        query = query.select_for_update(of=("self",))
    finding = get_object_or_404(query, id=identifier)
    job_for(user, finding.job.id)
    return finding


def review(user, finding, data):
    manual = finding.job.provider == "manual_visual_review"
    if not manual:
        require_mock_mode()
    if finding.review_status != "ready_for_review":
        raise RentalConflict(
            "This finding already has a preserved review. Rerun for a new version.",
            code="review_closed",
        )
    verdict = data.get("decision")
    if verdict not in {"accepted_as_observation", "rejected", "inconclusive"}:
        raise ValidationError(
            {
                "decision": "Accept as an advisory observation, reject, or mark inconclusive."
            }
        )
    if verdict == "accepted_as_observation" and (
        finding.uncertainty == "insufficient"
        or fingerprint(current_manifest(finding.job, user)) != finding.job.source_digest
    ):
        raise RentalConflict(
            "Insufficient or changed evidence cannot become an accepted observation.",
            code="source_changed",
        )
    if manual:
        sources = current_manifest(finding.job, user)
        required_ids = {media["id"] for row in sources for media in row["evidence"]}
        inspected = data.get("inspected_evidence_ids", [])
        if (
            not isinstance(inspected, list)
            or any(not isinstance(item, str) for item in inspected)
            or set(inspected) != required_ids
            or data.get("human_inspection_attested") is not True
            or fingerprint(sources) != finding.job.source_digest
        ):
            raise ValidationError(
                {
                    "inspected_evidence_ids": "Review the exact currently authorized source images before submitting a human observation."
                }
            )
        comparable = (
            all(row["evidence"] for row in sources)
            and data.get("comparison_quality") == "comparable"
            and data.get("identity_confirmed") is True
        )
        if verdict == "accepted_as_observation" and not comparable:
            raise ValidationError(
                {
                    "comparison_quality": "Insufficient or incomparable images cannot establish a visual observation."
                }
            )
        finding.output = {
            **finding.output,
            "comparison_basis": "human_inspected_sources",
            "reviewer_id": str(user.id),
            "inspection_attested_at": timezone.now().isoformat(),
            "inspected_evidence_ids": sorted(required_ids),
            "comparison_quality": data.get("comparison_quality", "inconclusive"),
            "identity_confirmed": data.get("identity_confirmed") is True,
            "independent_inspection": False,
            "liability_determined": False,
        }
        finding.uncertainty = "human_advisory" if comparable else "inconclusive"
    finding.review_note = text_field(data, "reason", required=True, limit=1200)
    finding.review_status, finding.reviewer, finding.reviewed_at = (
        verdict,
        user,
        timezone.now(),
    )
    finding.revision += 1
    finding.save()
    audit(finding, user, "asset_analysis_reviewed", finding.review_note)
    return finding


def finding_payload(row):
    return {
        "id": str(row.id),
        "job_id": str(row.job.id),
        "source_manifest": (
            row.job.source_manifest
            if row.job.provider == "manual_visual_review"
            else []
        ),
        "revision": row.revision,
        "kind": row.kind,
        "uncertainty": row.uncertainty,
        "output": row.output,
        "review_status": row.review_status,
        "review_note": row.review_note,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "allowed_actions": (
            ["read", "review"] if row.review_status == "ready_for_review" else ["read"]
        ),
    }


def payload(job, user):
    source_changed = fingerprint(current_manifest(job, user)) != job.source_digest
    return {
        "id": str(job.id),
        "asset_id": str(job.asset.id),
        "revision": job.revision,
        "state": job.state,
        "failure_code": job.failure_code,
        "source_digest": job.source_digest,
        "source_changed": source_changed,
        "previous_run_id": str(job.previous_run.id) if job.previous_run_id else "",
        "provider": job.provider,
        "provider_version": job.provider_version,
        "simulated": job.provider != "manual_visual_review",
        "source_manifest": job.source_manifest,
        "findings": [finding_payload(row) for row in job.suggestions.all()],
        "allowed_actions": ["read"]
        + (
            ["cancel"]
            if job.created_by_id == user.pk and job.state in {"queued", "processing"}
            else ["rerun"]
        ),
        "liability_determined": False,
    }
