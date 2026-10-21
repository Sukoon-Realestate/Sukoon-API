"""Metric alignment and conservative, observed free-space navigation.

No box or camera-path tube is treated as a room's walkable geometry. Cells need
observed ground, repeated free-space evidence and a clear body-sized volume.
"""

from collections import defaultdict, deque
import math
import numpy as np


def similarity(source, target):
    source, target = np.asarray(source, float), np.asarray(target, float)
    a, b = source.mean(0), target.mean(0)
    x, y = source - a, target - b
    if len(x) < 3 or np.linalg.matrix_rank(x, tol=1e-5) < 2:
        raise ValueError("degenerate_alignment")
    u, singular, vt = np.linalg.svd(y.T @ x / len(x))
    sign = np.ones(3)
    sign[-1] = np.sign(np.linalg.det(u @ vt))
    rotation = (u * sign) @ vt
    scale = float(np.dot(singular, sign) / np.mean(np.sum(x * x, axis=1)))
    translation = b - scale * rotation @ a
    return scale, rotation, translation


def transform_points(points, matrix):
    matrix = np.asarray(matrix, float).reshape(4, 4)
    return np.asarray(points) @ matrix[:3, :3].T + matrix[:3, 3]


def robust_alignment(scene_poses, capture_poses, threshold=.12):
    """Return scene -> capture similarity only after positional/rotation checks."""
    scene, capture = np.asarray(scene_poses), np.asarray(capture_poses)
    if len(scene) < 6:
        return {"status": "unverified", "reason": "insufficient_anchors"}
    a, b = scene[:, :3, 3], capture[:, :3, 3]
    if np.linalg.norm(np.ptp(b, axis=0)) < .5:
        return {"status": "unverified", "reason": "insufficient_baseline"}
    best = np.zeros(len(a), bool)
    random = np.random.default_rng(42)
    for _ in range(128):
        subset = random.choice(len(a), 3, replace=False)
        try:
            scale, rotation, translation = similarity(a[subset], b[subset])
        except (ValueError, np.linalg.LinAlgError):
            continue
        if not .02 < scale < 50:
            continue
        errors = np.linalg.norm(scale * a @ rotation.T + translation - b, axis=1)
        good = errors < threshold
        if good.sum() > best.sum():
            best = good
    if best.sum() < 6 or best.mean() < .8:
        return {"status": "unverified", "reason": "inconsistent_pose_priors"}
    scale, rotation, translation = similarity(a[best], b[best])
    errors = np.linalg.norm(scale * a @ rotation.T + translation - b, axis=1)
    angular = []
    for estimated, observed in zip(scene[best], capture[best]):
        delta = observed[:3, :3].T @ rotation @ estimated[:3, :3]
        angular.append(math.degrees(math.acos(np.clip((np.trace(delta) - 1) / 2, -1, 1))))
    if np.median(angular) > 8 or np.percentile(angular, 90) > 15:
        return {"status": "unverified", "reason": "orientation_disagreement"}
    matrix = np.eye(4)
    matrix[:3, :3], matrix[:3, 3] = scale * rotation, translation
    return {"status": "validated", "matrix": matrix.reshape(-1).tolist(),
            "scale": scale, "inliers": int(best.sum()), "anchors": len(a),
            "rmsMeters": float(np.sqrt(np.mean(errors[best] ** 2))),
            "rotationMedianDegrees": float(np.median(angular))}


def read_depth(path):
    """COLMAP's documented width&height&channels& float32 Fortran-order map."""
    with open(path, "rb") as handle:
        header = bytearray()
        while header.count(b"&") < 3 and len(header) < 100:
            byte = handle.read(1)
            if not byte:
                raise ValueError("invalid_depth_header")
            header.extend(byte)
        dimensions = header.decode("ascii").strip("&").split("&")
        if len(dimensions) != 3:
            raise ValueError("invalid_depth_header")
        width, height, channels = map(int, dimensions)
        if not (1 <= width <= 8192 and 1 <= height <= 8192 and channels == 1):
            raise ValueError("invalid_depth_dimensions")
        data = np.frombuffer(handle.read(width * height * 4 + 1), dtype="<f4")
        if data.size != width * height:
            raise ValueError("invalid_depth_bytes")
        return data.reshape((width, height), order="F").T.copy()


def navigation_from_depth(cameras, depths, *, metric_validated, cell=.20,
                          radius=.30, body_height=1.8, max_cells=2_000_000):
    if not metric_validated:
        return {"status": "needsReview", "reason": "metric_alignment_unverified", "cells": []}
    endpoints, origins, source_ids = [], [], []
    for index, camera in enumerate(cameras):
        depth = depths.get(camera["id"])
        if depth is None:
            continue
        height, width = depth.shape
        # Bound rays, while retaining observations across the entire image.
        step = max(1, math.ceil(max(width, height) / 160))
        y, x = np.mgrid[0:height:step, 0:width:step]
        z = depth[::step, ::step].reshape(-1)
        good = np.isfinite(z) & (z > .15) & (z < 12)
        scale_x, scale_y = width / camera["width"], height / camera["height"]
        k = np.asarray(camera["K"], float).reshape(3, 3).copy()
        k[0] *= scale_x
        k[1] *= scale_y
        rays = np.stack([x.reshape(-1), y.reshape(-1), np.ones(x.size)], axis=1) @ np.linalg.inv(k).T
        pose = np.asarray(camera["cameraToWorld"], float).reshape(4, 4)
        points = (rays[good] * z[good, None]) @ pose[:3, :3].T + pose[:3, 3]
        endpoints.append(points)
        origins.append(np.repeat(pose[None, :3, 3], len(points), axis=0))
        source_ids.extend([index] * len(points))
    if not endpoints:
        return {"status": "needsReview", "reason": "dense_geometry_unavailable", "cells": []}
    endpoints, origins = np.concatenate(endpoints), np.concatenate(origins)
    # Floor evidence must be repeated across views and near an actual horizontal
    # surface. The camera height supplies a plausibility interval, not a floor.
    camera_y = float(np.median([np.asarray(c["cameraToWorld"]).reshape(4, 4)[1, 3] for c in cameras]))
    plausible = endpoints[(endpoints[:, 1] < camera_y - .7) & (endpoints[:, 1] > camera_y - 2.3)]
    if len(plausible) < 100:
        return {"status": "needsReview", "reason": "floor_unobserved", "cells": []}
    histogram, edges = np.histogram(plausible[:, 1], bins=np.arange(camera_y - 2.3, camera_y - .65, .04))
    floor_y = float((edges[np.argmax(histogram)] + edges[np.argmax(histogram) + 1]) / 2)
    floor_points = endpoints[np.abs(endpoints[:, 1] - floor_y) < .055]
    if len(floor_points) < 100 or np.linalg.norm(np.ptp(floor_points[:, [0, 2]], axis=0)) < 1:
        return {"status": "needsReview", "reason": "floor_unreliable", "cells": []}
    occupied = {tuple(v) for v in np.floor(endpoints / cell).astype(int)}
    free = defaultdict(set)
    ground = defaultdict(set)
    for end, origin, source in zip(endpoints, origins, source_ids):
        if abs(end[1] - floor_y) < .055:
            ground[tuple(np.floor(end[[0, 2]] / cell).astype(int))].add(source)
        delta = end - origin
        distance = np.linalg.norm(delta)
        count = min(120, max(0, int((distance - .15) / (cell * .5))))
        if not count:
            continue
        positions = origin + np.linspace(0, max(0, 1 - .15 / distance), count)[:, None] * delta
        for voxel in set(map(tuple, np.floor(positions / cell).astype(int))):
            if voxel not in occupied:
                if len(free[voxel]) < 2:
                    free[voxel].add(source)
        if len(free) > max_cells:
            return {"status": "needsReview", "reason": "navigation_budget_exceeded", "cells": []}
    low = math.ceil((floor_y + .15) / cell)
    high = math.floor((floor_y + body_height) / cell)
    margin = math.ceil(radius / cell)
    offsets = [(x, z) for x in range(-margin, margin + 1) for z in range(-margin, margin + 1)
               if math.hypot(x, z) * cell <= radius + cell * .5]
    allowed = set()
    for (x, z), observations in ground.items():
        if len(observations) < 2:
            continue
        if all((x + dx, y, z + dz) not in occupied and len(free.get((x + dx, y, z + dz), ())) >= 2
               for dx, dz in offsets for y in range(low, high + 1)):
            allowed.add((x, z))
    # Components require observed open adjacency; never draw a straight path
    # between disconnected room islands or across a tracking reset.
    islands = []
    while allowed:
        first = min(allowed)
        queue, island = deque([first]), []
        allowed.remove(first)
        while queue:
            x, z = queue.popleft()
            island.append([x, z])
            for neighbour in ((x-1, z), (x+1, z), (x, z-1), (x, z+1)):
                if neighbour in allowed:
                    allowed.remove(neighbour)
                    queue.append(neighbour)
        if len(island) * cell * cell >= .5:
            islands.append(island)
    cells = [p for island in islands for p in island]
    return {"schemaVersion": 1, "status": "validated" if cells else "needsReview",
            "reason": "observed_free_volume" if cells else "insufficient_free_volume",
            "cellSizeMeters": cell, "floorY": floor_y, "eyeHeightMeters": 1.55,
            "bodyRadiusMeters": radius, "bodyHeightMeters": body_height,
            "cells": cells, "islands": islands, "areaSquareMeters": len(cells) * cell * cell,
            "evidence": {"rays": len(endpoints), "occupiedVoxels": len(occupied),
                         "observedFreeVoxels": len(free), "minimumViews": 2}}
