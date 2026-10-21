"""Calibrated spherical projection with observed-pixel mask, never generated fill.

The initial profile is deliberately review-only. AR rotation is a prior; feature
residuals, station translation and the coverage mask can reject it. Real-device
calibration of these thresholds remains a release gate.
"""

from collections import defaultdict
from io import BytesIO
import numpy as np
from PIL import Image
from . import storage


def _save(image):
    output = BytesIO()
    image.save(output, format="PNG")
    key, size, checksum = storage.write_blob([output.getvalue()], 30 * 1024**2)
    return {"blob": key, "size": size, "sha256": checksum, "mediaType": "image/png"}


def process(assets, cancelled):
    try:
        import cv2
    except ImportError:
        return {"status": "failed", "code": "PROCESSING_CAPACITY_UNAVAILABLE"}
    groups = defaultdict(list)
    for asset in assets:
        if asset.metadata["captureMode"] == "panorama360":
            groups[asset.metadata["stationId"]].append(asset)
    if not groups:
        return {"status": "needsCapture", "code": "PANORAMA_INCOMPLETE", "stations": []}
    results = []
    for station_id, frames in sorted(groups.items()):
        if cancelled():
            return {"status": "cancelled", "code": "PROCESSING_CANCELLED"}
        if len(frames) > 120:
            return {"status": "failed", "code": "PANORAMA_STATION_BUDGET_EXCEEDED"}
        results.append(stitch_station(station_id, frames, cv2, cancelled))
    return {
        "status": (
            "needsReview" if all(s["fullSphere"] for s in results) else "needsCapture"
        ),
        "code": (
            "OWNER_REVIEW_REQUIRED"
            if all(s["fullSphere"] for s in results)
            else "PANORAMA_INCOMPLETE"
        ),
        "stations": results,
        "hotspots": [],
        "linksRequireOwnerConfirmation": True,
    }


def stitch_station(station_id, frames, cv2, cancelled, width=2048):
    height = width // 2
    lon = (np.arange(width) + 0.5) / width * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(height) + 0.5) / height * np.pi
    xx, yy = np.meshgrid(lon, lat)
    world = np.stack(
        [np.sin(xx) * np.cos(yy), np.sin(yy), -np.cos(xx) * np.cos(yy)], axis=-1
    ).astype(np.float32)
    total = np.zeros((height, width, 3), np.float32)
    weights = np.zeros((height, width), np.float32)
    positions = []
    descriptors = []
    graph = {str(a.client_id): set() for a in frames}
    residuals = []
    orb = cv2.ORB_create(nfeatures=1600)
    for asset in frames:
        if cancelled():
            break
        m = asset.metadata
        pose = np.array(m["pose"]["matrix"]).reshape(4, 4)
        positions.append(pose[:3, 3])
        camera = m["camera"]
        rgb = np.array(Image.open(storage.read_path(asset.blob)).convert("RGB"))
        image_height, image_width = rgb.shape[:2]
        rays = world @ pose[:3, :3]
        z = rays[:, :, 2]
        denominator = np.maximum(z, 1e-6)
        u = (camera["fx"] * rays[:, :, 0] / denominator + camera["cx"]).astype(
            np.float32
        )
        v = (camera["fy"] * rays[:, :, 1] / denominator + camera["cy"]).astype(
            np.float32
        )
        valid = (
            (z > 0)
            & (u >= 1)
            & (u < image_width - 2)
            & (v >= 1)
            & (v < image_height - 2)
        )
        weight = np.where(valid, np.maximum(z, 0) ** 4, 0).astype(np.float32)
        warped = cv2.remap(rgb, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        total += warped * weight[:, :, None]
        weights += weight
        # Match content, not only frusta. Unmatched frames never establish a
        # connected station. No AI imagery or orientation changes are inserted.
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        scale = min(1, 800 / max(gray.shape))
        gray = cv2.resize(gray, None, fx=scale, fy=scale)
        keypoints, desc = orb.detectAndCompute(gray, None)
        if desc is not None:
            intr = np.array(
                [
                    [camera["fx"] * scale, 0, camera["cx"] * scale],
                    [0, camera["fy"] * scale, camera["cy"] * scale],
                    [0, 0, 1],
                ]
            )
            rays_at = (
                np.array([[*k.pt, 1] for k in keypoints])
                @ np.linalg.inv(intr).T
                @ pose[:3, :3].T
            )
            rays_at /= np.linalg.norm(rays_at, axis=1)[:, None]
            # Match nearby orientations and a loop-closure anchor. Bound CPU and
            # descriptor memory independently of a malicious upload count.
            candidates = descriptors[-12:]
            if len(descriptors) > 12:
                candidates = [descriptors[0], *candidates]
            for other_id, other_desc, other_rays in candidates:
                if cancelled():
                    return {
                        "id": station_id,
                        "fullSphere": False,
                        "status": "cancelled",
                    }
                matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(
                    desc, other_desc, k=2
                )
                good = [
                    pair[0]
                    for pair in matches
                    if len(pair) == 2 and pair[0].distance < 0.7 * pair[1].distance
                ]
                if len(good) < 20:
                    continue
                errors = np.degrees(
                    np.arccos(
                        np.clip(
                            [
                                np.dot(rays_at[x.queryIdx], other_rays[x.trainIdx])
                                for x in good
                            ],
                            -1,
                            1,
                        )
                    )
                )
                if np.median(errors) < 2 and np.percentile(errors, 90) < 4:
                    graph[str(asset.client_id)].add(other_id)
                    graph[other_id].add(str(asset.client_id))
                    residuals.extend(errors.tolist())
            descriptors.append((str(asset.client_id), desc, rays_at))
    mask = weights > 1e-6
    pixels = np.clip(total / np.maximum(weights[:, :, None], 1e-6), 0, 255).astype(
        np.uint8
    )
    seen = set()
    pending = [str(frames[0].client_id)]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(graph[node] - seen)
    translated = max(
        (float(np.linalg.norm(p - positions[0])) for p in positions), default=0
    )
    bands = [float(b.mean()) for b in np.array_split(mask, 6)]
    full = bool(
        mask.mean() >= 0.999
        and min(bands) >= 0.995
        and translated <= 0.08
        and len(seen) == len(frames)
        and len(residuals) > 0
    )
    return {
        "id": station_id,
        "roomId": frames[0].metadata["roomId"],
        "fullSphere": full,
        "status": "needsReview" if full else "needsCapture",
        "observedFraction": float(mask.mean()),
        "verticalBands": bands,
        "stationTranslationMeters": translated,
        "connectedFrames": len(seen),
        "inputFrames": len(frames),
        "rotationResidualMedianDegrees": (
            float(np.median(residuals)) if residuals else None
        ),
        "projection": "equirectangular-rhs-y-up",
        "resources": {
            "image": _save(Image.fromarray(pixels)),
            "mask": _save(Image.fromarray(mask.astype(np.uint8) * 255)),
        },
    }
