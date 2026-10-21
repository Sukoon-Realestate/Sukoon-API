"""Train actual anisotropic Gaussians with pinned gsplat; export standard PLY.

CPU reference rendering is an explicit small numerical-test mode. The production
worker selects CUDA gsplat and never substitutes reference results for a scan.
"""

from pathlib import Path
import math
import numpy as np
from PIL import Image

SH0 = 0.28209479177387814


def write_ply(path, parameters, maximum):
    means = parameters["means"].detach().cpu().numpy()
    scales = parameters["scales"].detach().cpu().numpy()
    quats = parameters["quats"].detach().cpu().numpy()
    quats /= np.maximum(np.linalg.norm(quats, axis=1, keepdims=True), 1e-8)
    opacity = parameters["opacities"].detach().cpu().numpy().reshape(-1, 1)
    colors = parameters["sh0"].detach().cpu().numpy().reshape(-1, 3)
    finite = np.isfinite(np.c_[means, scales, quats, opacity, colors]).all(1)
    indices = np.flatnonzero(finite & (opacity[:, 0] > -5))
    if len(indices) > maximum:
        # Deterministic coverage-preserving spatial buckets before opacity rank.
        span = np.maximum(np.ptp(means[indices], axis=0), 1e-5)
        bins = np.floor((means[indices] - means[indices].min(0)) / span * 64).astype(int)
        order = np.lexsort((-opacity[indices, 0], bins[:, 2], bins[:, 1], bins[:, 0]))
        first = np.unique(bins[order], axis=0, return_index=True)[1]
        selected = indices[order[first]]
        remaining = np.setdiff1d(indices, selected)
        remaining = remaining[np.argsort(-opacity[remaining, 0])]
        indices = np.r_[selected[:maximum], remaining[:max(0, maximum-len(selected))]]
    if not len(indices):
        raise ValueError("EMPTY_GAUSSIAN_SCENE")
    data = np.c_[means[indices], np.zeros((len(indices), 3)), colors[indices],
                 opacity[indices], scales[indices], quats[indices]].astype("<f4")
    names = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2",
             "opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    header = "ply\nformat binary_little_endian 1.0\n" + f"element vertex {len(indices)}\n"
    header += "".join(f"property float {name}\n" for name in names) + "end_header\n"
    with open(path, "wb") as stream:
        stream.write(header.encode("ascii"))
        stream.write(data.tobytes())
    return len(indices)


def reference_render(params, view, intrinsic, width, height):
    """Small differentiable reference used by numerical tests, never a worker fallback."""
    import torch
    if len(params["means"]) > 128 or width * height > 4096:
        raise ValueError("REFERENCE_RENDER_BUDGET")
    positions = params["means"] @ view[:3, :3].T + view[:3, 3]
    depth = positions[:, 2].clamp(min=.01)
    pixels = positions @ intrinsic.T
    pixels = pixels[:, :2] / depth[:, None]
    sigma = torch.exp(params["scales"]).mean(1) * intrinsic[0, 0] / depth
    y, x = torch.meshgrid(torch.arange(height, device=depth.device), torch.arange(width, device=depth.device), indexing="ij")
    delta = torch.stack([x, y], -1)[None] - pixels[:, None, None]
    alpha = torch.sigmoid(params["opacities"])[:, None, None] * torch.exp(-delta.square().sum(-1) / (2 * sigma[:, None, None].square().clamp(min=.25)))
    alpha = (alpha * (positions[:, 2] > .05)[:, None, None]).clamp(max=.99)
    order = torch.argsort(depth)
    alpha = alpha[order]
    transmittance = torch.cumprod(torch.cat([torch.ones_like(alpha[:1]), 1-alpha[:-1]], 0), dim=0)
    color = (params["sh0"].reshape(-1, 3) * SH0 + .5).clamp(0, 1)[order]
    return ((alpha * transmittance)[..., None] * color[:, None, None]).sum(0)


def train(component, image_dir, output, config, event):
    import torch
    import gsplat
    from scipy.spatial import cKDTree
    from gsplat import rasterization, DefaultStrategy

    if torch.__version__.split("+")[0] != "2.7.1" or gsplat.__version__ != "1.5.3":
        raise ValueError("GAUSSIAN_VERSION_MISMATCH")
    if not torch.cuda.is_available():
        raise RuntimeError("GPU_RUNTIME_UNAVAILABLE")
    torch.cuda.set_per_process_memory_fraction(config["gpuMemoryFraction"])
    torch.manual_seed(42)
    random = np.random.default_rng(42)
    with np.load(Path(component["directory"]) / "initial.npz") as initial:
        points, colors = initial["points"], initial["colors"]
    if len(points) > config["maxGaussians"] // 2:
        selected = random.choice(len(points), config["maxGaussians"] // 2, replace=False)
        points, colors = points[selected], colors[selected]
    distances, _ = cKDTree(points).query(points, k=min(4, len(points)))
    scales = np.maximum(distances[:, 1:].mean(1), 1e-4)
    quaternion = np.zeros((len(points), 4), np.float32)
    quaternion[:, 0] = 1
    values = {"means": points, "scales": np.repeat(np.log(scales)[:, None], 3, axis=1),
              "quats": quaternion, "opacities": np.full(len(points), -2., np.float32),
              "sh0": ((colors.astype(np.float32) / 255 - .5) / SH0)[:, None]}
    params = {key: torch.nn.Parameter(torch.tensor(value, dtype=torch.float32, device="cuda")) for key, value in values.items()}
    scene_scale = max(.1, float(np.linalg.norm(np.ptp(points, axis=0))))
    rates = {"means": .00016 * scene_scale, "scales": .005, "quats": .001, "opacities": .05, "sh0": .0025}
    optimizers = {key: torch.optim.Adam([value], lr=rates[key], eps=1e-15) for key, value in params.items()}
    strategy = DefaultStrategy(refine_start_iter=500, refine_stop_iter=min(4000, config["trainSteps"]-1),
                               refine_every=100, reset_every=3000, verbose=False)
    strategy.check_sanity(params, optimizers)
    strategy_state = strategy.initialize_state(scene_scale=scene_scale)
    cameras = sorted(component["cameras"], key=lambda c: c["imageName"])
    held = cameras[::8] if len(cameras) >= 12 else cameras[-1:]
    held_ids = {c["id"] for c in held}
    training = [c for c in cameras if c["id"] not in held_ids]
    cached = {}

    def image_for(camera):
        if camera["id"] not in cached:
            with Image.open(Path(image_dir) / camera["imageName"]) as image:
                size = image.size
                scale = min(1., config["trainingEdge"] / max(size))
                width, height = round(size[0] * scale), round(size[1] * scale)
                pixels = np.array(image.resize((width, height), Image.Resampling.LANCZOS)).astype(np.float32) / 255
            k = np.asarray(camera["K"], np.float32).reshape(3, 3).copy()
            k[0] *= width / size[0]
            k[1] *= height / size[1]
            cached[camera["id"]] = (torch.from_numpy(pixels), k)
            if len(cached) > 8:
                cached.pop(next(iter(cached)))
        return cached[camera["id"]]

    def render(camera, gradients):
        pixels, k = image_for(camera)
        height, width = pixels.shape[:2]
        view = np.linalg.inv(np.asarray(camera["cameraToWorld"]).reshape(4, 4))
        rendered, alpha, info = rasterization(
            means=params["means"], quats=params["quats"], scales=torch.exp(params["scales"]),
            opacities=torch.sigmoid(params["opacities"]), colors=params["sh0"], sh_degree=0,
            viewmats=torch.tensor(view[None], device="cuda", dtype=torch.float32),
            Ks=torch.tensor(k[None], device="cuda", dtype=torch.float32), width=width, height=height,
            packed=False, near_plane=.05, far_plane=100., absgrad=gradients,
        )
        return rendered[0], pixels.to("cuda"), info

    event("training_gaussians", iteration=0, iterations=config["trainSteps"])
    for step in range(config["trainSteps"]):
        camera = training[int(random.integers(len(training)))]
        prediction, target, info = render(camera, True)
        strategy.step_pre_backward(params, optimizers, strategy_state, step, info)
        # Photometric fidelity, with bounded scale/opacity regularization. No
        # generative prior invents unseen property surfaces.
        loss = (prediction - target).abs().mean() + .0001 * torch.exp(params["scales"]).mean()
        if not torch.isfinite(loss):
            raise ValueError("GAUSSIAN_OPTIMIZATION_DIVERGED")
        loss.backward()
        for optimizer in optimizers.values():
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        if len(params["means"]) < config["maxGaussians"]:
            strategy.step_post_backward(params, optimizers, strategy_state, step, info)
        if len(params["means"]) > config["maxGaussians"] * 2:
            raise ValueError("GAUSSIAN_POINT_BUDGET_EXCEEDED")
        if step % 100 == 0:
            event("training_gaussians", iteration=step, iterations=config["trainSteps"])
    event("validating_held_out_views")
    psnr = []
    with torch.no_grad():
        for index, camera in enumerate(held):
            prediction, target, _ = render(camera, False)
            error = float((prediction - target).square().mean())
            psnr.append(-10 * math.log10(max(error, 1e-10)))
            if index == 0:
                Image.fromarray((prediction.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)).save(Path(output) / "preview.jpg", quality=90)
    quality = []
    for name, maximum in [("preview", 20000), ("detail", config["maxGaussians"])]:
        count = write_ply(Path(output) / f"{name}.ply", params, maximum)
        quality.append({"name": name, "file": f"{name}.ply", "gaussians": count})
    return {"qualityLevels": quality, "heldOutViews": len(held), "heldOutPsnrMean": float(np.mean(psnr)),
            "iterations": config["trainSteps"], "representation": "anisotropic-gaussians-sh0",
            "appearanceValidated": float(np.mean(psnr)) >= 22,
            "gpuPeakAllocatedBytes": torch.cuda.max_memory_allocated(), "device": torch.cuda.get_device_name()}
