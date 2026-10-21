"""Validate evidence, never infer room completeness from a frame count."""

import math
import re
import uuid
import numpy as np
from .errors import require

MODES = ("walkthrough3d", "panorama360")
POLICY = "rgb-tracking-v1"
CONVENTION = "rhs-y-up-optical-camera-v1"
PART_BYTES = 1024 * 1024
MAX_ASSET = 30 * 1024 * 1024


def fields(value, required, optional=()):
    require(
        isinstance(value, dict)
        and set(required) <= set(value)
        and set(value) <= set(required) | set(optional),
        "MANIFEST_INVALID",
        "Invalid capture document fields.",
    )


def identifier(value):
    try:
        return str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def frame(value):
    fields(
        value,
        {
            "schemaVersion",
            "frameId",
            "roomId",
            "trackingSegmentId",
            "coordinateFrameId",
            "captureMode",
            "timestampMonotonicNs",
            "image",
            "camera",
            "pose",
            "quality",
            "depth",
        },
        {"stationId"},
    )
    require(
        value["schemaVersion"] == 1 and value["captureMode"] in MODES,
        "MANIFEST_INVALID",
        "Unsupported capture schema or mode.",
    )
    for key in ("frameId", "roomId", "trackingSegmentId", "coordinateFrameId"):
        require(identifier(value[key]), "MANIFEST_INVALID", "Invalid capture identity.")
    require(
        value["coordinateFrameId"] == value["trackingSegmentId"],
        "MANIFEST_INVALID",
        "Tracking reset must have a distinct coordinate frame.",
    )
    require(
        isinstance(value["timestampMonotonicNs"], str)
        and re.fullmatch(r"[1-9][0-9]{0,19}", value["timestampMonotonicNs"]),
        "MANIFEST_INVALID",
        "A precise monotonic source timestamp is required.",
    )
    if value["captureMode"] == "panorama360":
        require(
            identifier(value.get("stationId")),
            "MANIFEST_INVALID",
            "Station identity is required.",
        )
    else:
        require(
            "stationId" not in value,
            "MANIFEST_INVALID",
            "Walkthrough frames have no station.",
        )
    image = value["image"]
    fields(image, {"width", "height", "sha256", "orientationApplied"})
    require(
        all(
            type(image[k]) is int and 240 <= image[k] <= 8192
            for k in ("width", "height")
        )
        and image["width"] * image["height"] <= 24_000_000
        and isinstance(image["sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", image["sha256"])
        and image["orientationApplied"] == "sensor_native",
        "MANIFEST_INVALID",
        "Invalid original image dimensions or calibration orientation.",
    )
    camera = value["camera"]
    fields(
        camera,
        {
            "calibrationId",
            "model",
            "fx",
            "fy",
            "cx",
            "cy",
            "physicalLensId",
            "distortionHandling",
        },
    )
    require(
        all(finite(camera[k]) for k in ("fx", "fy", "cx", "cy"))
        and image["width"] * 0.05 <= camera["fx"] <= image["width"] * 20
        and image["height"] * 0.05 <= camera["fy"] <= image["height"] * 20
        and 0 <= camera["cx"] <= image["width"]
        and 0 <= camera["cy"] <= image["height"]
        and camera["model"] == "pinhole"
        and camera["distortionHandling"]
        in ("sdk_rectified", "sdk_intrinsics_unverified")
        and all(
            isinstance(camera[k], str) and 1 <= len(camera[k]) <= 120
            for k in ("calibrationId", "physicalLensId")
        ),
        "MANIFEST_INVALID",
        "Invalid image-space calibration.",
    )
    pose = value["pose"]
    fields(pose, {"convention", "matrix", "trackingState", "source", "mapRevision"})
    matrix = pose["matrix"]
    require(
        isinstance(matrix, list) and len(matrix) == 16 and all(map(finite, matrix)),
        "MANIFEST_INVALID",
        "Invalid camera transform.",
    )
    m = np.array(matrix).reshape(4, 4)
    require(
        np.allclose(m[3], [0, 0, 0, 1], atol=1e-5)
        and np.allclose(m[:3, :3].T @ m[:3, :3], np.eye(3), atol=1e-3)
        and abs(np.linalg.det(m[:3, :3]) - 1) < 1e-3
        and np.max(np.abs(m[:3, 3])) <= 10_000
        and pose["convention"] == "T_world_camera_optical_row_major"
        and pose["source"] in ("arcore", "arkit")
        and pose["trackingState"] == "tracking"
        and type(pose["mapRevision"]) is int
        and pose["mapRevision"] >= 0,
        "MANIFEST_INVALID",
        "Camera transform must be a tracked right-handed rigid pose.",
    )
    quality = value["quality"]
    fields(
        quality,
        {
            "accepted",
            "policyVersion",
            "syncOffsetMs",
            "sharpness",
            "darkFraction",
            "clippedFraction",
            "featureIds",
        },
    )
    require(
        quality["accepted"] is True
        and quality["policyVersion"] == POLICY
        and finite(quality["syncOffsetMs"])
        and abs(quality["syncOffsetMs"]) <= 5
        and all(
            finite(quality[k]) for k in ("sharpness", "darkFraction", "clippedFraction")
        )
        and quality["sharpness"] >= 35
        and 0 <= quality["darkFraction"] <= 0.65
        and 0 <= quality["clippedFraction"] <= 0.65
        and isinstance(quality["featureIds"], list)
        and len(quality["featureIds"]) <= 256
        and all(
            isinstance(v, str) and re.fullmatch(r"[0-9]{1,20}", v)
            for v in quality["featureIds"]
        ),
        "MANIFEST_INVALID",
        "Original frame lacks synchronized quality evidence.",
    )
    require(
        value["depth"] is None,
        "MANIFEST_INVALID",
        "This profile uses RGB without depth.",
    )
    return value


def manifest(value, session):
    fields(
        value,
        {
            "schemaVersion",
            "sessionId",
            "propertyId",
            "requestedOutputs",
            "capturePolicyVersion",
            "coordinateConvention",
            "roomIds",
            "frameIds",
        },
    )
    require(
        value["schemaVersion"] == 1
        and value["sessionId"] == str(session.id)
        and value["propertyId"] == str(session.property.id)
        and value["requestedOutputs"] == list(MODES)
        and value["capturePolicyVersion"] == POLICY
        and value["coordinateConvention"] == CONVENTION,
        "MANIFEST_INVALID",
        "Capture scope or policy does not match.",
    )
    for key, maximum in (("roomIds", 40), ("frameIds", 5000)):
        values = value[key]
        require(
            isinstance(values, list)
            and 0 < len(values) <= maximum
            and all(map(identifier, values))
            and len(set(values)) == len(values),
            "MANIFEST_INVALID",
            "Capture references must be unique scoped IDs.",
        )
    rooms = set(
        str(v)
        for v in session.rooms.filter(confirmed=True).values_list(
            "client_id", flat=True
        )
    )
    require(
        set(value["roomIds"]) <= rooms,
        "MANIFEST_INVALID",
        "Confirm every captured room first.",
    )
    assets = list(
        session.assets.filter(client_id__in=value["frameIds"], state="verified")
    )
    require(
        len(assets) == len(value["frameIds"]),
        "ASSET_NOT_VERIFIED",
        "Verify all originals before processing.",
    )
    require(
        {a.metadata["roomId"] for a in assets} == set(value["roomIds"]),
        "MANIFEST_INVALID",
        "Frames must belong to the selected rooms.",
    )
    # Every station and tracking segment belongs to one room/mode; map-reset
    # components are preserved, never joined by an assumed identity transform.
    stations = {}
    timestamps = set()
    for asset in assets:
        m = frame(asset.metadata)
        identity = (m["trackingSegmentId"], m["timestampMonotonicNs"])
        require(
            identity not in timestamps,
            "MANIFEST_INVALID",
            "Duplicate source-frame timestamp.",
        )
        timestamps.add(identity)
        if m["captureMode"] == "panorama360":
            owner = (m["roomId"], m["trackingSegmentId"])
            require(
                stations.setdefault(m["stationId"], owner) == owner,
                "MANIFEST_INVALID",
                "A station cannot cross rooms or tracking resets.",
            )
    return value
