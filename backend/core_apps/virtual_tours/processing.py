import copy
import logging
import uuid
from django.db import transaction
from django.utils import timezone
from .errors import require
from .models import TourRevision, TourVariant
from .panorama import process_panorama
from .validation import validate_authoring, validate_glb, validate_walk, validate_spawns
from .contracts import DELIVERY, MOVEMENT
from .schemas import validate_schema
from .processing_lease import ProcessingLease, ProcessingSuperseded

PROCESSOR_VERSION = "sokoun-tours-1"
logger = logging.getLogger(__name__)


def build_variants(revision, heartbeat=lambda: None):
    heartbeat()
    if revision.capture_job_id:
        from .capture_delivery import build_variants as build_capture_variants
        return build_capture_variants(revision)
    document = copy.deepcopy(revision.authoring)
    source_hash, scopes = validate_authoring(revision, document)
    require(
        source_hash == revision.source_hash,
        "source_changed",
        "Inventory scope or source assets changed. Process a new draft.",
        409,
    )
    assets = {str(a.id): a for a in revision.assets.all()}
    outputs = {}
    variants = []
    for spec in document["variants"]:
        heartbeat()
        resources = {}
        spaces = [s for s in document["spaces"] if s["id"] in spec["space_ids"]]
        manifest = {
            k: document[k]
            for k in (
                "schema_version",
                "kind",
                "title",
                "captured_at",
                "content_origin",
            )
        }
        manifest.update(
            revision_id=str(revision.id),
            scope_fingerprint=scopes[spec["context"]],
            spaces=spaces,
        )
        if document["kind"] == "panorama_360":
            scenes = []
            for scene in document["scenes"]:
                if scene["id"] not in spec["scene_ids"]:
                    continue
                asset_id = scene["source_asset_id"]
                if asset_id not in outputs:
                    outputs[asset_id] = process_panorama(
                        assets[asset_id], heartbeat=heartbeat
                    )
                resource_id = uuid.uuid4().hex
                resources[resource_id] = outputs[asset_id]
                scenes.append(
                    {
                        "id": scene["id"],
                        "space_id": scene["space_id"],
                        "initial_view": scene["initial_view"],
                        "projection": "cubemap",
                        "tile_set_resource_id": resource_id,
                        "faces": outputs[asset_id]["faces"],
                        "levels": [
                            {"size": s, "tile_size": 512}
                            for s in outputs[asset_id]["levels"]
                        ],
                    }
                )
            manifest.update(
                scenes=scenes,
                start_scene_id=spec["start_scene_id"],
                hotspots=[
                    h
                    for h in document["hotspots"]
                    if h["source_scene_id"] in spec["scene_ids"]
                    and h["target_scene_id"] in spec["scene_ids"]
                ],
            )
        else:
            manifest.update(
                coordinate_system=document["coordinate_system"],
                spawns=spec["spawns"],
                start_spawn_id=spec["start_spawn_id"],
                movement=MOVEMENT,
                camera={"vertical_fov_deg": 65, "near_m": 0.05, "far_m": 100},
                interaction={
                    "free_fly": False,
                    "floor_transition": "approved_spawn_only",
                },
            )
            total = 0
            for role in ("visual", "collision", "walk"):
                heartbeat()
                asset = assets[spec[f"{role}_asset_id"]]
                total += asset.size
                if role == "walk":
                    validate_walk(asset, spec, spaces)
                else:
                    validate_glb(asset, collision=role == "collision")
                resource_id = uuid.uuid4().hex
                resources[resource_id] = {
                    "blob": asset.blob,
                    "media_type": asset.media_type,
                    "type": "file",
                }
                manifest[role] = {"resource_id": resource_id, "bytes": asset.size}
            require(
                total <= 12 * 1024**2,
                "delivery_budget",
                "This single-model viewer loads all essential assets initially. Reduce the complete package to at most 12 MiB.",
            )
            validate_spawns(assets[spec["collision_asset_id"]], spec)
        validate_schema(
            {
                **manifest,
                "session_id": str(uuid.uuid4()),
                "variant_id": str(uuid.uuid4()),
            },
            DELIVERY,
        )
        variants.append(
            dict(
                context=spec["context"],
                scope_fingerprint=scopes[spec["context"]],
                source_hash=source_hash,
                manifest=manifest,
                resources=resources,
            )
        )
    return variants


def process_revision(revision_id, expected_hash):
    with transaction.atomic():
        revision = (
            TourRevision.objects.select_for_update(of=("self",))
            .select_related("tour__property")
            .get(id=revision_id)
        )
        if (
            revision.source_hash != expected_hash
            or revision.processing_state != "queued"
        ):
            return
        revision.processing_state, revision.stage = (
            "processing",
            "validating_and_building",
        )
        revision.processing_token = uuid.uuid4()
        recoveries = revision.report.get("worker_recoveries", 0)
        revision.report = {"worker_recoveries": recoveries} if recoveries else {}
        revision.save(update_fields=[
            "processing_state", "processing_token", "stage", "report", "updated_at"
        ])
    lease = ProcessingLease(revision)
    try:
        variants = build_variants(revision, heartbeat=lease.heartbeat)
    except ProcessingSuperseded:
        return
    except Exception as exc:
        from .errors import TourError

        # Do not include source paths or provider credentials in user-visible errors.
        code = exc.default_code if isinstance(exc, TourError) else "processing_failed"
        message = (
            str(exc.detail)
            if isinstance(exc, TourError)
            else "Processing failed. Retry processing or contact support."
        )
        TourRevision.objects.filter(
            id=revision_id, source_hash=expected_hash, processing_state="processing",
            processing_token=lease.token,
        ).update(
            processing_state="failed",
            processing_token=None,
            stage="failed",
            report={**revision.report, "code": code, "message": message},
            updated_at=timezone.now(),
        )
        logger.warning(
            "tour_processing_failed revision=%s error_type=%s code=%s",
            revision_id, type(exc).__name__, code,
        )
        return
    with transaction.atomic():
        current = TourRevision.objects.select_for_update(of=("self",)).get(
            id=revision_id
        )
        if (
            current.source_hash != expected_hash
            or current.processing_state != "processing"
            or current.processing_token != lease.token
        ):
            return
        current.variants.all().delete()
        TourVariant.objects.bulk_create(
            [TourVariant(revision=current, **v) for v in variants]
        )
        current.processing_state, current.stage = "ready", "ready_for_preview"
        current.processing_token = None
        current.processor_version = PROCESSOR_VERSION
        current.report = {"variant_count": len(variants), "source_hash": expected_hash}
        current.save(
            update_fields=[
                "processing_state",
                "processing_token",
                "stage",
                "processor_version",
                "report",
                "updated_at",
            ]
        )
