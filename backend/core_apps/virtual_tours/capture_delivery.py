"""Turn reviewed capture outputs into ordinary, immutable tour revisions.

No output is published by processing or selection. The existing owner-submit /
staff-review path still applies, including inventory scope and revocation.
"""

import copy
import hashlib
import json
import uuid
from datetime import date

import numpy as np
from PIL import Image

from . import storage
from .capture_contracts import CAPTURE_AUTHORING, CAPTURE_DELIVERY
from .errors import require
from .policy import digest, scope_policy
from .schemas import unique, validate_schema


def source(revision):
    job = revision.capture_job
    require(job is not None, "capture_source_missing", "Choose a capture result.", 409)
    session = job.manifest.session
    require(
        not job.cancel_requested and session.deleted_at is None
        and session.property_id == revision.tour.property_id
        and session.owner_id == session.property.owner_id
        and session.property.retired_at is None
        and job.state in {"needs_capture", "needs_review", "completed"},
        "capture_source_unavailable", "The capture source is no longer available.", 409,
    )
    return job


def validate(revision, document):
    validate_schema(document, CAPTURE_AUTHORING)
    job = source(revision)
    require(document["kind"] == revision.tour.kind, "invalid_kind", "The tour kind cannot change.")
    require(date.fromisoformat(document["captured_at"]) <= date.today(), "invalid_capture_date", "Capture date cannot be in the future.")
    components = {c["id"]: c for c in job.outputs.get("walkthrough3d", {}).get("components", [])}
    stations = {s["id"]: s for s in job.outputs.get("panorama360", {}).get("stations", [])}
    unique(document["spaces"])
    unique(document["variants"], "context")
    unique(document["hotspots"])
    spaces = {s["id"]: s for s in document["spaces"]}
    confirmed = {str(r.client_id) for r in job.manifest.session.rooms.filter(confirmed=True)}
    require(set(spaces) <= confirmed, "capture_room_unconfirmed", "Confirm the captured rooms before selection.", 409)
    selected_components, selected_stations = set(document["component_ids"]), set(document["station_ids"])
    require(len(selected_components) == len(document["component_ids"]) and len(selected_stations) == len(document["station_ids"]), "duplicate_output", "Choose each output once.")
    require(selected_components <= components.keys() and selected_stations <= stations.keys(), "foreign_capture_output", "Choose outputs of this immutable capture job.", 403)
    require((bool(selected_components) if document["kind"] == "model_3d" else not selected_components and len(selected_stations) >= 2), "capture_selection_incomplete", "Choose a 3D component or at least two complete panorama stations.")
    require(document["content_origin"] == ("reality_scan" if selected_components else "photographic_capture"), "invalid_origin", "Capture output provenance cannot change.")
    covered = set()
    for identity in selected_components:
        component = components[identity]
        require({"preview", "detail", "cameras", "navigation"} <= component.get("resources", {}).keys(), "capture_output_incomplete", "This component has no complete renderable output.", 409)
        require(component.get("status") == "needsReview", "capture_output_incomplete", "This component is not ready for review.", 409)
        covered.update(component["roomIds"])
    for identity in selected_stations:
        station = stations[identity]
        require(station.get("fullSphere") is True and station.get("status") == "needsReview", "panorama_incomplete", "Incomplete spheres cannot become tour scenes.", 409)
        covered.add(station["roomId"])
    require(covered == set(spaces), "capture_scope_incomplete", "Map every captured room, without adding unrelated spaces.")
    scopes = {}
    used_components, used_stations = set(), set()
    for spec in document["variants"]:
        cs, ss, room_ids = set(spec["component_ids"]), set(spec["station_ids"]), set(spec["space_ids"])
        require(len(cs) == len(spec["component_ids"]) and len(ss) == len(spec["station_ids"]) and len(room_ids) == len(spec["space_ids"]), "duplicate_output", "Variant selections must be unique.")
        require(cs <= selected_components and ss <= selected_stations and room_ids <= spaces.keys() and spec["start_place_id"] in cs | ss, "capture_scope_invalid", "Select known outputs and a starting place.")
        rooms = {room for c in cs for room in components[c]["roomIds"]} | {stations[s]["roomId"] for s in ss}
        # A Gaussian component cannot be cropped by a room label. Its complete
        # set of rooms must be permitted by the selected inventory context.
        require(rooms == room_ids, "scope_violation", "A component includes all of its rooms.", 403)
        scopes[spec["context"]] = scope_policy(revision.tour.target, spec["context"], [spaces[r] for r in sorted(rooms)])
        used_components |= cs
        used_stations |= ss
    require(used_components == selected_components and used_stations == selected_stations, "capture_scope_incomplete", "Every selected output needs a viewing scope.")
    for link in document["hotspots"]:
        require(link["source_scene_id"] in selected_stations and link["target_scene_id"] in selected_stations and link["source_scene_id"] != link["target_scene_id"], "invalid_hotspot", "Confirm links between selected stations only.")
    return digest({"authoring": document, "manifest": job.manifest.sha256, "profile": job.profile,
                   "outputs": job.outputs, "scopes": scopes}), scopes


def publishable(revision):
    job = source(revision)
    selected = set(revision.authoring["component_ids"])
    require(all(c.get("quality", {}).get("appearanceValidated") is True for c in job.outputs.get("walkthrough3d", {}).get("components", []) if c["id"] in selected),
            "capture_quality_review", "The held-out image quality check has not passed. Recapture or reprocess this component.", 409)


def verified_bytes(resource, limit):
    require(0 < resource.get("size", 0) <= limit, "delivery_budget", "The output exceeds the delivery budget.")
    file = storage.read_path(resource["blob"])
    require(file.stat().st_size == resource["size"], "capture_integrity_failed", "The output size changed.", 409)
    data = file.read_bytes()
    require(hashlib.sha256(data).hexdigest() == resource["sha256"], "capture_integrity_failed", "The output checksum changed.", 409)
    return data


def gaussian_count(resource, maximum):
    data = verified_bytes(resource, 32 * 1024**2)
    end = data.find(b"end_header\n", 0, 4096)
    require(end > 0, "invalid_gaussian", "A bounded Gaussian PLY header is required.")
    header = data[:end].decode("ascii").splitlines()
    names = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2", "opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    require(len(header) == 20 and header[:2] == ["ply", "format binary_little_endian 1.0"] and header[2].startswith("element vertex ") and header[3:] == [f"property float {name}" for name in names], "invalid_gaussian", "Use the captured SH0 Gaussian format.")
    count = int(header[2].split()[-1])
    payload = data[end + len(b"end_header\n"):]
    require(0 < count <= maximum and len(payload) == count * len(names) * 4, "delivery_budget", "Invalid Gaussian count or payload length.")
    points = np.frombuffer(payload, dtype="<f4").reshape(count, len(names))
    require(np.isfinite(points).all() and (np.abs(points[:, :3]) < 10000).all()
            and (points[:, 10:13] < 5).all() and (points[:, 10:13] > -20).all()
            and (np.linalg.norm(points[:, 13:17], axis=1) > .5).all(), "invalid_gaussian", "Invalid Gaussian geometry.")
    return count


def rigid_or_similarity(matrix):
    value = np.asarray(matrix, dtype=float).reshape(4, 4)
    rotation = value[:3, :3]
    scale = np.linalg.norm(rotation, axis=0)
    require(np.isfinite(value).all() and np.allclose(value[3], [0, 0, 0, 1])
            and (scale > .02).all() and (scale < 50).all()
            and np.allclose(scale, scale[0], rtol=.01)
            and np.allclose((rotation / scale).T @ (rotation / scale), np.eye(3), atol=.01)
            and np.linalg.det(rotation) > 0, "invalid_alignment", "The capture transform is not a validated similarity.")
    return value.reshape(-1).tolist()


def build_variants(revision):
    document = revision.authoring
    source_hash, scopes = validate(revision, document)
    require(source_hash == revision.source_hash, "source_changed", "The selected output changed.", 409)
    job = source(revision)
    components = {c["id"]: c for c in job.outputs.get("walkthrough3d", {}).get("components", [])}
    stations = {s["id"]: s for s in job.outputs.get("panorama360", {}).get("stations", [])}
    results = []
    # Validate once; variants may share private immutable bytes, never scopes.
    checked = {}
    for identity in document["component_ids"]:
        c = components[identity]
        resources = c["resources"]
        checked[identity] = {
            "preview": gaussian_count(resources["preview"], 20000),
            "detail": gaussian_count(resources["detail"], 120000),
            "cameras": json.loads(verified_bytes(resources["cameras"], 1024**2)),
        }
        nav = json.loads(verified_bytes(resources["navigation"], 8 * 1024**2))
        require(nav.get("status") == c["navigationStatus"], "invalid_navigation", "Navigation evidence changed.")
        if nav.get("status") == "validated":
            require(c["scaleStatus"] == "validated_metric" and 0 < nav.get("cellSizeMeters", 0) <= .25
                    and nav.get("bodyRadiusMeters", 0) >= .25 and nav.get("bodyHeightMeters", 0) >= 1.75
                    and nav.get("evidence", {}).get("minimumViews", 0) >= 2
                    and 0 < len(nav.get("cells", [])) <= 200000, "invalid_navigation", "Walkable cells require observed, metric free-space evidence.")
    for spec in document["variants"]:
        resources = {}
        def attach(resource):
            identity = uuid.uuid4().hex
            resources[identity] = {"blob": resource["blob"], "type": "file", "media_type": resource["mediaType"]}
            return {"resource_id": identity, "bytes": resource["size"], "sha256": resource["sha256"]}
        manifest = {k: copy.deepcopy(document[k]) for k in ("kind", "title", "captured_at", "content_origin")}
        manifest.update(schema_version=2, representation="gaussian_capture", revision_id=str(revision.id),
                        scope_fingerprint=scopes[spec["context"]], coordinate_system="right_handed_y_up", free_fly=False,
                        spaces=[s for s in document["spaces"] if s["id"] in spec["space_ids"]],
                        components=[], stations=[], alignments=[], start_place_id=spec["start_place_id"],
                        hotspots=[h for h in document["hotspots"] if h["source_scene_id"] in spec["station_ids"] and h["target_scene_id"] in spec["station_ids"]])
        for identity in spec["component_ids"]:
            c, check = components[identity], checked[identity]
            cameras = [{"id": cam["id"], "space_id": cam["roomId"], "matrix": rigid_or_similarity(cam["cameraToWorld"])} for cam in check["cameras"]]
            require(all(cam["space_id"] in c["roomIds"] for cam in cameras)
                    and c["defaultCameraId"] in {cam["id"] for cam in cameras}, "invalid_camera", "Camera scope or starting pose is invalid.")
            manifest["components"].append({"id": identity, "space_ids": c["roomIds"],
                "label": {"ar": f"جزء {len(manifest['components']) + 1}", "en": f"Component {len(manifest['components']) + 1}"},
                "preview": attach(c["resources"]["preview"]), "detail": attach(c["resources"]["detail"]),
                "preview_gaussians": check["preview"], "detail_gaussians": check["detail"],
                "cameras": cameras, "default_camera_id": c["defaultCameraId"],
                "navigation": attach(c["resources"]["navigation"]), "navigation_status": c["navigationStatus"],
                "scale_status": "metric" if c["scaleStatus"] == "validated_metric" else "unverified"})
            for station_id, transform in c.get("stationToSceneTransforms", {}).items():
                if station_id in spec["station_ids"] and transform.get("status") == "validated":
                    manifest["alignments"].append({"station_id": station_id, "component_id": identity,
                                                   "matrix": rigid_or_similarity(transform["matrix"])})
        for identity in spec["station_ids"]:
            station = stations[identity]
            image = station["resources"]["image"]
            verified_bytes(image, 30 * 1024**2)
            with Image.open(storage.read_path(image["blob"])) as decoded:
                width, height = decoded.size
                require(width in (2048, 4096) and width == height * 2, "invalid_panorama", "Use a calibrated 2:1 panorama.")
                decoded.verify()
            manifest["stations"].append({"id": identity, "space_id": station["roomId"], "image": attach(image),
                                        "width": width, "height": height, "full_sphere": True,
                                        "initial_view": {"yaw_rad": 0, "pitch_rad": 0, "hfov_rad": 1.4}})
        validate_schema({**manifest, "session_id": str(uuid.uuid4()), "variant_id": str(uuid.uuid4())}, CAPTURE_DELIVERY)
        results.append({"context": spec["context"], "scope_fingerprint": scopes[spec["context"]],
                        "source_hash": source_hash, "manifest": manifest, "resources": resources})
    return results
