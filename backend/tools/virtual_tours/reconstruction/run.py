"""Bounded reconstruction entry point invoked by the private capture worker."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from . import ENGINE_VERSION
from .geometry import navigation_from_depth, read_depth, transform_points
from .sfm import reconstruct


def event(stage, **values):
    print(json.dumps({"stage": stage, **values}), flush=True)


def artifact(path, kind):
    path = Path(path)
    return {"file": path.name, "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mediaType": kind}


def dense_geometry(component, images, directory, config):
    import pycolmap
    colmap = shutil.which("colmap")
    if not colmap:
        return {"status": "needsReview", "reason": "dense_runtime_unavailable", "cells": []}
    version = subprocess.run([colmap, "-h"], capture_output=True, text=True, timeout=20)
    if "COLMAP 3.12.6" not in version.stdout + version.stderr:
        raise ValueError("DENSE_COLMAP_VERSION_MISMATCH")
    dense = Path(directory) / "dense"
    event("estimating_dense_geometry")
    pycolmap.undistort_images(str(dense), component["directory"], str(images),
        undistort_options=pycolmap.UndistortCameraOptions(max_image_size=config["depthEdge"]))
    with (Path(directory) / "dense.log").open("w") as log:
        subprocess.run([colmap, "patch_match_stereo", "--workspace_path", str(dense),
            "--workspace_format", "COLMAP", "--PatchMatchStereo.geom_consistency", "true",
            "--PatchMatchStereo.max_image_size", str(config["depthEdge"]),
            "--PatchMatchStereo.num_iterations", "5"], check=True, stdout=log, stderr=log,
            timeout=config["denseSeconds"])
    # Undistortion may change calibration/crop. Use its camera model and poses,
    # rather than attaching the original image K to a different depth grid.
    reconstruction = pycolmap.Reconstruction(str(dense / "sparse"))
    by_name = {camera["imageName"]: camera for camera in component["cameras"]}
    cameras, depths = [], {}
    for image in reconstruction.images.values():
        source = by_name.get(image.name)
        path = dense / "stereo" / "depth_maps" / f"{image.name}.geometric.bin"
        if source is None or not path.is_file():
            continue
        calibration = reconstruction.cameras[image.camera_id]
        camera = {**source, "width": calibration.width, "height": calibration.height,
                  "K": calibration.calibration_matrix().reshape(-1).tolist()}
        cameras.append(camera)
        depths[camera["id"]] = read_depth(path)
    event("validating_navigation")
    return navigation_from_depth(cameras, depths, metric_validated=component["metricValidated"])


def execute(document, directory):
    import torch
    from .gaussian import train

    started = time.monotonic()
    directory = Path(directory)
    config = document["configuration"]
    frames = document["frames"]
    walked = [f for f in frames if f["metadata"]["captureMode"] == "walkthrough3d"]
    if len(walked) < 8:
        return {"status": "needsCapture", "code": "INSUFFICIENT_TRANSLATIONAL_VIEWS", "components": []}
    if len(frames) > config["maxFrames"]:
        return {"status": "needsReview", "code": "PROCESSING_INPUT_BUDGET_EXCEEDED", "components": []}
    components, images = reconstruct(frames, directory, config, event)
    if not components:
        return {"status": "needsCapture", "code": "CAMERA_REGISTRATION_FAILED", "components": []}
    cuda = torch.cuda.is_available()
    results = []
    for component in components:
        output = Path(component["directory"]) / "output"
        output.mkdir()
        result = {key: component[key] for key in ["id", "scaleStatus", "registeredFrames", "inputFrames",
                  "registeredFraction", "points", "reprojectionMedianPixels", "bounds", "captureToSceneTransforms"]}
        result.update({"coordinateConvention": "right-handed-y-up-optical-cameras",
                       "status": "needsProcessing", "code": "GPU_RUNTIME_UNAVAILABLE", "resources": {},
                       "roomIds": sorted({c["roomId"] for c in component["cameras"]}), "stationToSceneTransforms": {}})
        for frame in frames:
            metadata = frame["metadata"]
            station = metadata.get("stationId")
            alignment = component["captureToSceneTransforms"].get(metadata["trackingSegmentId"], {})
            if not station or station in result["stationToSceneTransforms"] or alignment.get("status") != "validated":
                continue
            # Spherical images are projected in capture-world axes, not in the
            # first phone camera's rotated optical axes.
            capture = np.eye(4)
            capture[:3, 3] = np.asarray(metadata["pose"]["matrix"]).reshape(4, 4)[:3, 3]
            result["stationToSceneTransforms"][station] = {
                "status": "validated", "matrix": (np.asarray(alignment["matrix"]).reshape(4, 4) @ capture).reshape(-1).tolist()}
        (output / "cameras.json").write_text(json.dumps(component["cameras"]))
        result["resources"]["cameras"] = artifact(output / "cameras.json", "application/json")
        navigation = {"status": "needsReview", "reason": "dense_runtime_unavailable", "cells": []}
        if cuda:
            try:
                navigation = dense_geometry(component, images, directory, config)
            except (ValueError, subprocess.SubprocessError):
                navigation = {"status": "needsReview", "reason": "dense_reconstruction_failed", "cells": []}
            event("training_gaussians")
            try:
                quality = train(component, images, output, config, event)
                result.update({"status": "needsReview", "code": "OWNER_REVIEW_REQUIRED", "quality": quality})
                for level in quality["qualityLevels"]:
                    result["resources"][level["name"]] = artifact(output / level["file"], "application/octet-stream")
                result["resources"]["thumbnail"] = artifact(output / "preview.jpg", "image/jpeg")
            except torch.cuda.OutOfMemoryError:
                result.update(status="failed", code="GPU_MEMORY_EXHAUSTED")
                torch.cuda.empty_cache()
            except (RuntimeError, ValueError) as error:
                code = str(error)
                result.update(status="failed", code=code if code.isupper() and len(code) < 80 else "GAUSSIAN_TRAINING_FAILED")
        (output / "navigation.json").write_text(json.dumps(navigation))
        result["resources"]["navigation"] = artifact(output / "navigation.json", "application/json")
        result["navigationStatus"] = navigation["status"]
        result["navigationReason"] = navigation["reason"]
        result["defaultCameraId"] = component["cameras"][0]["id"]
        result["outputDirectory"] = str(output.relative_to(directory))
        results.append(result)
    available = any("preview" in c["resources"] for c in results)
    return {"status": "needsReview" if available else "needsProcessing",
            "code": "OWNER_REVIEW_REQUIRED" if available else "GPU_RUNTIME_UNAVAILABLE",
            "engineVersion": ENGINE_VERSION, "components": results,
            "alignment": "connected" if len(results) == 1 else "disconnected_components",
            "navigation": "validated" if all(c["navigationStatus"] == "validated" for c in results) else "needsReview",
            "elapsedSeconds": round(time.monotonic()-started, 3),
            "configurationHash": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()}


if __name__ == "__main__":
    task = Path(sys.argv[1]).resolve()
    os.umask(0o077)
    document = json.loads(task.read_text())
    try:
        result = execute(document, task.parent)
    except Exception as error:
        code = str(error)
        result = {"status": "failed", "code": code if code.isupper() and len(code) < 80 else "RECONSTRUCTION_FAILED", "components": []}
        # Diagnostics are private worker files, never property content or secrets.
        import traceback
        (task.parent / "failure.log").write_text(traceback.format_exc())
    (task.parent / "result.json").write_text(json.dumps(result, allow_nan=False))
    event("reconstruction_complete")
