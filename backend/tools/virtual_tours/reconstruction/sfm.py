"""Real, calibrated COLMAP camera estimation; AR poses remain checked priors."""

from collections import defaultdict
from pathlib import Path
import json
import numpy as np
from PIL import Image
from .geometry import robust_alignment


def pose_matrix(image):
    result = np.eye(4)
    result[:3] = image.cam_from_world().inverse().matrix()
    return result


def reconstruct(frames, directory, config, event):
    import pycolmap as colmap

    if colmap.__version__ != "3.12.6":
        raise ValueError("COLMAP_VERSION_MISMATCH")
    directory = Path(directory)
    images = directory / "images"
    images.mkdir()
    groups, records = defaultdict(list), {}
    for index, frame in enumerate(sorted(frames, key=lambda f: int(f["metadata"]["timestampMonotonicNs"]))):
        metadata = frame["metadata"]
        camera = metadata["camera"]
        name = f'{index:06d}-{metadata["frameId"]}.jpg'
        with Image.open(frame["path"]) as source:
            rgb = source.convert("RGB")
            width, height = rgb.size
            ratio = min(1., config["imageEdge"] / max(width, height))
            target = (round(width * ratio), round(height * ratio))
            rgb = rgb.resize(target, Image.Resampling.LANCZOS)
            rgb.save(images / name, quality=95, subsampling=0)
        sx, sy = target[0] / width, target[1] / height
        intrinsics = [camera["fx"] * sx, camera["fy"] * sy, camera["cx"] * sx, camera["cy"] * sy]
        calibration = (camera["calibrationId"], camera["physicalLensId"], *target, *[round(x, 6) for x in intrinsics])
        groups[calibration].append(name)
        records[name] = {"metadata": metadata, "intrinsics": intrinsics, "size": target}
    database = str(directory / "database.db")
    device = colmap.Device.cuda if colmap.has_cuda else colmap.Device.cpu
    event("extracting_features")
    for calibration, names in groups.items():
        reader = colmap.ImageReaderOptions(camera_model="PINHOLE", camera_params=",".join(map(str, calibration[-4:])))
        colmap.extract_features(database, str(images), image_names=names,
            camera_mode=colmap.CameraMode.SINGLE, camera_model="PINHOLE", reader_options=reader,
            sift_options=colmap.SiftExtractionOptions(max_num_features=4096, max_image_size=config["imageEdge"], num_threads=2), device=device)
    event("matching_features")
    # Exhaustive verified matches include doorway transitions and loop closures;
    # no assumed identity alignment is inserted at tracking-component boundaries.
    colmap.match_exhaustive(database, device=device,
        sift_options=colmap.SiftMatchingOptions(num_threads=2),
        matching_options=colmap.ExhaustiveMatchingOptions(block_size=16))
    event("estimating_cameras")
    sparse = directory / "sparse"
    sparse.mkdir()
    options = colmap.IncrementalPipelineOptions(
        num_threads=2, min_model_size=6, max_num_models=8,
        ba_refine_focal_length=False, ba_refine_principal_point=False, ba_refine_extra_params=False,
    )
    options.mapper.init_min_tri_angle = 4
    models = colmap.incremental_mapping(database, str(images), str(sparse), options=options)
    components = []
    for index, model in sorted(models.items(), key=lambda item: -item[1].num_reg_images()):
        registered = [image for image in model.images.values() if image.has_pose]
        if len(registered) < 6 or model.num_points3D() < 100:
            continue
        segment_images = defaultdict(list)
        for image in registered:
            segment_images[records[image.name]["metadata"]["trackingSegmentId"]].append(image)
        anchors = []
        for segment, values in segment_images.items():
            alignment = robust_alignment(
                [pose_matrix(image) for image in values],
                [np.asarray(records[image.name]["metadata"]["pose"]["matrix"]).reshape(4, 4) for image in values],
            )
            anchors.append((segment, alignment))
        valid = [(segment, a) for segment, a in anchors if a["status"] == "validated"]
        primary = max(valid, key=lambda item: item[1]["inliers"], default=None)
        if primary:
            model.transform(colmap.Sim3d(np.asarray(primary[1]["matrix"]).reshape(4, 4)[:3]))
        else:
            # Orient the preview using one observed camera, without declaring
            # metric scale or a verified relationship between other segments.
            first = registered[0]
            measured = np.asarray(records[first.name]["metadata"]["pose"]["matrix"]).reshape(4, 4)
            current = pose_matrix(first)
            rotation = measured[:3, :3] @ current[:3, :3].T
            transform = np.c_[rotation, -rotation @ current[:3, 3]]
            model.transform(colmap.Sim3d(transform))
        component_dir = directory / f"component-{index}"
        component_dir.mkdir()
        model.write(str(component_dir))
        transforms = {}
        cameras = []
        for segment, values in segment_images.items():
            # Re-estimate against the final scene. Direction is explicitly
            # capture -> scene and may contain a scale, not just a rigid pose.
            alignment = robust_alignment(
                [pose_matrix(image) for image in values],
                [np.asarray(records[image.name]["metadata"]["pose"]["matrix"]).reshape(4, 4) for image in values],
            )
            if alignment["status"] == "validated":
                alignment["matrix"] = np.linalg.inv(np.asarray(alignment["matrix"]).reshape(4, 4)).reshape(-1).tolist()
                alignment["direction"] = "capture_to_scene"
            transforms[segment] = alignment
        for image in registered:
            camera = model.cameras[image.camera_id]
            metadata = records[image.name]["metadata"]
            cameras.append({"id": metadata["frameId"], "imageName": image.name,
                "roomId": metadata["roomId"], "trackingSegmentId": metadata["trackingSegmentId"],
                "stationId": metadata.get("stationId"), "width": camera.width, "height": camera.height,
                "K": camera.calibration_matrix().reshape(-1).tolist(),
                "cameraToWorld": pose_matrix(image).reshape(-1).tolist()})
        points = np.array([p.xyz for p in model.points3D.values()], np.float32)
        colors = np.array([p.color for p in model.points3D.values()], np.uint8)
        errors = np.array([p.error for p in model.points3D.values()])
        finite = np.isfinite(points).all(1) & np.isfinite(errors) & (errors <= 3)
        np.savez(component_dir / "initial.npz", points=points[finite], colors=colors[finite])
        report = {"id": f"component-{index}", "directory": str(component_dir), "cameras": cameras,
            "captureToSceneTransforms": transforms, "metricValidated": bool(primary),
            "scaleStatus": "validated_metric" if primary else "arbitrary",
            "registeredFrames": len(registered), "inputFrames": len(frames),
            "registeredFraction": len(registered) / len(frames), "points": int(finite.sum()),
            "reprojectionMedianPixels": float(np.median(errors[finite])) if finite.any() else None,
            "bounds": {"min": np.percentile(points[finite], 1, axis=0).tolist(),
                       "max": np.percentile(points[finite], 99, axis=0).tolist()}}
        (component_dir / "cameras.json").write_text(json.dumps(report))
        components.append(report)
    return components, images
