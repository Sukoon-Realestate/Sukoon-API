"""Lease-aware adapter for the real, isolated COLMAP/gsplat runtime."""

import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import shutil
from django.conf import settings
from . import storage


def configuration():
    return {"engine": "colmap-3.12.6-gsplat-1.5.3-v1", "maxFrames": 300,
            "imageEdge": 1600, "trainingEdge": 800, "depthEdge": 800,
            "trainSteps": 7000, "maxGaussians": 120000,
            "gpuMemoryFraction": .8, "denseSeconds": 900,
            "seconds": 3600, "maxOutputBytes": 128 * 1024**2}


def profile_identity():
    identity = {
        "configuration": configuration(),
        "enabled": getattr(settings, "CAPTURE_RECONSTRUCTION_ENABLED", False),
        "runtime": getattr(settings, "CAPTURE_RECONSTRUCTION_PYTHON", ""),
        "colmap": getattr(settings, "CAPTURE_RECONSTRUCTION_COLMAP", ""),
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    return f"rgb-dual-v2-{digest}"


def runtime_status():
    """Probe only an explicitly configured, credential-free GPU worker runtime."""
    if not getattr(settings, "CAPTURE_RECONSTRUCTION_ENABLED", False):
        return {"available": False, "code": "GPU_RUNTIME_NOT_CONFIGURED"}
    python = getattr(settings, "CAPTURE_RECONSTRUCTION_PYTHON", "")
    colmap = getattr(settings, "CAPTURE_RECONSTRUCTION_COLMAP", "")
    if not python or not Path(python).is_file() or not os.access(python, os.X_OK):
        return {"available": False, "code": "GPU_PYTHON_RUNTIME_UNAVAILABLE"}
    if not colmap or not Path(colmap).is_file() or not os.access(colmap, os.X_OK):
        return {"available": False, "code": "COLMAP_RUNTIME_UNAVAILABLE"}
    try:
        version = subprocess.run([colmap, "-h"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "code": "COLMAP_RUNTIME_UNAVAILABLE"}
    if "COLMAP 3.12.6" not in version.stdout + version.stderr:
        return {"available": False, "code": "COLMAP_VERSION_MISMATCH"}
    env = {
        key: os.environ[key]
        for key in ["PATH", "LANG", "CUDA_HOME", "CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "TORCH_CUDA_ARCH_LIST"]
        if key in os.environ
    }
    env["PATH"] = str(Path(colmap).resolve().parent) + os.pathsep + env.get("PATH", "")
    probe = (
        "import torch, pycolmap, gsplat; "
        "assert torch.__version__.split('+')[0] == '2.7.1'; "
        "assert pycolmap.__version__ == '3.12.6'; "
        "assert gsplat.__version__ == '1.5.3'; "
        "assert torch.cuda.is_available() and pycolmap.has_cuda"
    )
    try:
        result = subprocess.run(
            [python, "-c", probe], cwd=settings.BASE_DIR, env=env,
            capture_output=True, text=True, timeout=25,
        )
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "code": "GPU_PYTHON_RUNTIME_UNAVAILABLE"}
    if result.returncode:
        return {"available": False, "code": "GPU_RUNTIME_UNAVAILABLE"}
    return {"available": True, "code": "GPU_RUNTIME_AVAILABLE"}


def terminate(process):
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def process(assets, cancelled, progress, config=None):
    config = config or configuration()
    walkthrough = [a for a in assets if a.metadata["captureMode"] == "walkthrough3d"]
    if len(walkthrough) < 8:
        return {"status": "needsCapture", "code": "INSUFFICIENT_TRANSLATIONAL_VIEWS", "components": []}
    if len(assets) > config["maxFrames"]:
        return {"status": "needsReview", "code": "PROCESSING_INPUT_BUDGET_EXCEEDED", "components": []}
    python = getattr(settings, "CAPTURE_RECONSTRUCTION_PYTHON", "") or sys.executable
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="sokoun-reconstruction-") as temporary:
        directory = Path(temporary)
        originals = directory / "originals"
        originals.mkdir()
        frames = []
        for asset in assets:
            if cancelled():
                return {"status": "cancelled", "code": "PROCESSING_CANCELLED", "components": []}
            target = originals / f"{asset.client_id}.jpg"
            source = storage.read_path(asset.blob)
            # A verified original stays immutable; workers only derive new files.
            with source.open("rb") as incoming, target.open("xb") as outgoing:
                checksum = hashlib.sha256()
                while chunk := incoming.read(1024 * 1024):
                    checksum.update(chunk)
                    outgoing.write(chunk)
            if checksum.hexdigest() != asset.sha256:
                return {"status": "failed", "code": "ORIGINAL_INTEGRITY_FAILED", "components": []}
            frames.append({"path": str(target), "metadata": asset.metadata})
        (directory / "task.json").write_text(json.dumps({"configuration": config, "frames": frames}))
        # No server/AI/storage credentials are inherited by the reconstruction
        # subprocess. Only runtime/library locations and device selection pass.
        env = {key: os.environ[key] for key in ["PATH", "LANG", "CUDA_HOME", "CUDA_VISIBLE_DEVICES",
               "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "TORCH_CUDA_ARCH_LIST"] if key in os.environ}
        colmap = getattr(settings, "CAPTURE_RECONSTRUCTION_COLMAP", "")
        if colmap:
            env["PATH"] = str(Path(colmap).resolve().parent) + os.pathsep + env.get("PATH", "")
        env.update(OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", PYTHONUNBUFFERED="1")
        with (directory / "runtime.log").open("w") as log:
            child = subprocess.Popen([python, "-m", "tools.virtual_tours.reconstruction.run", str(directory / "task.json")],
                cwd=settings.BASE_DIR, env=env, stdout=subprocess.PIPE, stderr=log, start_new_session=True)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            buffer = b""
            try:
                while child.poll() is None:
                    if cancelled() or time.monotonic()-started > config["seconds"]:
                        terminate(child)
                        return {"status": "cancelled", "code": "PROCESSING_CANCELLED", "components": []}
                    for key, _ in selector.select(timeout=2):
                        block = os.read(key.fd, 8192)
                        if not block:
                            selector.unregister(key.fileobj)
                            continue
                        buffer += block
                        if len(buffer) > 16384:
                            buffer = b""
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            try:
                                message = json.loads(line)
                                stage = message.get("stage", "")
                                if stage in {"extracting_features", "matching_features", "estimating_cameras", "estimating_dense_geometry",
                                             "validating_navigation", "training_gaussians", "validating_held_out_views", "reconstruction_complete"}:
                                    progress(stage)
                            except (ValueError, TypeError, AttributeError):
                                pass
                output = directory / "result.json"
                if child.returncode != 0 or not output.is_file() or output.stat().st_size > 10 * 1024**2:
                    return {"status": "failed", "code": "RECONSTRUCTION_RUNTIME_FAILED", "components": []}
                result = json.loads(output.read_text())
                total = 0
                for component in result.get("components", []):
                    folder = (directory / component.pop("outputDirectory")).resolve()
                    if directory not in folder.parents:
                        raise ValueError("Invalid reconstruction output directory")
                    for resource in component.get("resources", {}).values():
                        file = folder / resource.pop("file")
                        if file.is_symlink() or file.resolve().parent != folder:
                            raise ValueError("Invalid reconstruction artifact")
                        total += file.stat().st_size
                        if total > config["maxOutputBytes"] or cancelled():
                            raise ValueError("Reconstruction artifact budget exceeded")
                        key, size, checksum = storage.write_blob(storage.file_chunks(file), config["maxOutputBytes"])
                        if checksum != resource["sha256"] or size != resource["size"]:
                            raise ValueError("Reconstruction artifact integrity failure")
                        resource["blob"] = key
                return result
            finally:
                terminate(child)
                selector.close()
                child.stdout.close()
