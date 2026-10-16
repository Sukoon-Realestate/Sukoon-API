import copy
import io
import json
import math
import struct
import subprocess
from datetime import date
from django.conf import settings
from PIL import Image
from .errors import require
from .policy import digest, scope_policy
from .schemas import WALK, connected, unique, validate_schema
from .storage import read_path as path


def validate_authoring(revision, document):
    validate_schema(document)
    require(
        document["kind"] == revision.tour.kind,
        "invalid_kind",
        "Revision kind cannot change.",
    )
    require(
        date.fromisoformat(document["captured_at"]) <= date.today(),
        "invalid_capture_date",
        "Capture date cannot be in the future.",
    )
    unique(document["spaces"])
    unique(document["variants"], "context")
    spaces = {s["id"]: s for s in document["spaces"]}
    assets = {str(a.id): a for a in revision.assets.all()}
    used = set()

    def asset(identity, role):
        require(
            identity in assets and assets[identity].role == role,
            "foreign_asset",
            "Use a completed asset belonging to this revision.",
            403,
        )
        used.add(identity)

    if document["kind"] == "panorama_360":
        unique(document["scenes"])
        unique(document["hotspots"])
        for scene in document["scenes"]:
            require(
                scene["space_id"] in spaces,
                "invalid_space",
                "Scene space does not exist.",
            )
            asset(scene["source_asset_id"], "panorama")
        connected(document["scenes"], document["hotspots"], document["scenes"][0]["id"])
    contexts = {}
    for variant in document["variants"]:
        require(
            len(set(variant["space_ids"])) == len(variant["space_ids"])
            and set(variant["space_ids"]).issubset(spaces),
            "invalid_space",
            "Variant spaces must be unique and known.",
        )
        selected = [spaces[i] for i in variant["space_ids"]]
        contexts[variant["context"]] = scope_policy(
            revision.tour.target, variant["context"], selected
        )
        if document["kind"] == "panorama_360":
            scenes = [s for s in document["scenes"] if s["id"] in variant["scene_ids"]]
            require(
                len(scenes)
                == len(set(variant["scene_ids"]))
                == len(variant["scene_ids"]),
                "invalid_scene",
                "Variant scenes must be unique and known.",
            )
            require(
                all(s["space_id"] in variant["space_ids"] for s in scenes),
                "scope_violation",
                "Scene is outside the variant.",
            )
            hotspots = [
                h
                for h in document["hotspots"]
                if h["source_scene_id"] in variant["scene_ids"]
                and h["target_scene_id"] in variant["scene_ids"]
            ]
            connected(scenes, hotspots, variant["start_scene_id"])
        else:
            for role in ("visual", "collision", "walk"):
                asset(variant[f"{role}_asset_id"], role)
            unique(variant["spawns"])
            require(
                variant["start_spawn_id"] in {s["id"] for s in variant["spawns"]},
                "invalid_spawn",
                "Choose an existing start spawn.",
            )
            for spawn in variant["spawns"]:
                require(
                    spawn["space_id"] in variant["space_ids"]
                    and spawn["floor_id"] == spaces[spawn["space_id"]]["floor_id"],
                    "invalid_spawn",
                    "Spawn must belong to a permitted space and floor.",
                )
    return (
        digest(
            {
                "authoring": document,
                "assets": {i: assets[i].sha256 for i in sorted(used)},
                "scopes": contexts,
            }
        ),
        contexts,
    )


def validate_glb(asset, collision=False):
    file = path(asset.blob)
    with file.open("rb") as handle:
        header = handle.read(20)
        require(len(header) == 20, "invalid_glb", "GLB header is incomplete.")
        magic, version, length, chunk_length, chunk_type = struct.unpack(
            "<IIIII", header
        )
        require(
            magic == 0x46546C67
            and version == 2
            and length == asset.size
            and chunk_type == 0x4E4F534A
            and chunk_length < min(asset.size, 8 * 1024**2),
            "invalid_glb",
            "Only complete GLB 2.0 files are accepted.",
        )
        try:
            doc = json.loads(handle.read(chunk_length))
        except (ValueError, UnicodeError):
            require(False, "invalid_glb", "Invalid GLB JSON chunk.")
    require(
        doc.get("asset", {}).get("version") == "2.0",
        "invalid_glb",
        "GLB version must be 2.0.",
    )

    def inspect(value):
        if isinstance(value, dict):
            require(
                "uri" not in value,
                "external_resource",
                "GLB resources must be embedded buffer views; URIs are forbidden.",
            )
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    inspect(doc)
    require(
        not doc.get("animations") and not doc.get("skins"),
        "unsupported_geometry",
        "Bake animation and skin transforms before uploading.",
    )
    require(
        not doc.get("extensionsRequired"),
        "unsupported_extension",
        "Export an uncompressed, self-contained GLB without required extensions.",
    )
    nodes = doc.get("nodes", [])
    require(len(nodes) <= 2000, "geometry_budget", "Reduce the number of scene nodes.")
    if collision:
        require(
            not doc.get("images") and not doc.get("textures"),
            "invalid_collision",
            "Collision GLB must contain geometry only.",
        )
    for node in nodes:
        require(
            node.get("scale", [1, 1, 1]) == [1, 1, 1] and "matrix" not in node,
            "unsafe_transform",
            "Bake scale and matrix transforms into mesh coordinates.",
        )
    accessors = doc.get("accessors", [])
    triangles = 0
    mesh_triangles = []
    for mesh in doc.get("meshes", []):
        count = 0
        for primitive in mesh.get("primitives", []):
            require(
                primitive.get("mode", 4) == 4,
                "unsupported_geometry",
                "Only triangle meshes are supported.",
            )
            idx = primitive.get(
                "indices", primitive.get("attributes", {}).get("POSITION", -1)
            )
            require(
                isinstance(idx, int) and 0 <= idx < len(accessors),
                "invalid_glb",
                "Missing triangle accessor.",
            )
            count += accessors[idx].get("count", 0) // 3
        mesh_triangles.append(count)
    # Count instances, including unused meshes conservatively. A tiny mesh
    # instanced thousands of times must not evade the triangle budget.
    triangles = sum(mesh_triangles)
    instances = {}
    for node in nodes:
        if isinstance(node.get("mesh"), int):
            instances[node["mesh"]] = instances.get(node["mesh"], 0) + 1
    triangles += sum(
        mesh_triangles[i] * max(0, n - 1)
        for i, n in instances.items()
        if 0 <= i < len(mesh_triangles)
    )
    require(
        0 < triangles <= (50000 if collision else 200000),
        "geometry_budget",
        "Reduce mesh complexity before processing.",
    )
    require(
        asset.size <= (5 if collision else 20) * 1024**2,
        "delivery_budget",
        "Prepared visual GLB must be at most 20 MiB; collider at most 5 MiB.",
    )
    command = settings.VIRTUAL_TOUR_GLTF_VALIDATOR
    require(
        bool(command),
        "validator_unconfigured",
        "Configure the Khronos glTF validator on the processing worker.",
        503,
    )
    # Executable path is deployment-owned; no shell or uploaded command text.
    result = subprocess.run(
        [command, str(file)], capture_output=True, timeout=90, check=False
    )
    require(
        result.returncode == 0,
        "gltf_validation_failed",
        "Khronos validation failed. Check the prepared GLB.",
    )
    if doc.get("images"):
        # Validate the embedded decoded texture budget, not merely file size.
        with file.open("rb") as handle:
            handle.seek(20 + chunk_length)
            binary_header = handle.read(8)
            require(
                len(binary_header) == 8
                and struct.unpack("<II", binary_header)[1] == 0x004E4942,
                "invalid_glb",
                "Missing embedded binary chunk.",
            )
            binary_start = handle.tell()
            pixels = 0
            require(
                len(doc["images"]) <= 32, "texture_budget", "Use at most 32 textures."
            )
            for texture in doc["images"]:
                view = doc["bufferViews"][texture["bufferView"]]
                handle.seek(binary_start + view.get("byteOffset", 0))
                with Image.open(io.BytesIO(handle.read(view["byteLength"]))) as image:
                    require(
                        image.format in ("JPEG", "PNG") and max(image.size) <= 2048,
                        "texture_budget",
                        "Use embedded JPEG/PNG textures of at most 2048 pixels per edge.",
                    )
                    pixels += image.width * image.height
                    require(
                        pixels <= 32_000_000,
                        "texture_budget",
                        "Reduce total decoded texture pixels.",
                    )
                    image.load()
    return {"triangles": triangles, "bytes": asset.size}


def validate_spawns(asset, variant):
    command = settings.VIRTUAL_TOUR_SPAWN_VALIDATOR
    require(
        bool(command),
        "validator_unconfigured",
        "Configure the collision and spawn validator on the worker.",
        503,
    )
    result = subprocess.run(
        [command, str(path(asset.blob))],
        input=json.dumps({"spawns": variant["spawns"]}).encode(),
        capture_output=True,
        timeout=90,
        check=False,
    )
    require(
        result.returncode == 0,
        "invalid_spawn",
        "A starting place intersects collision geometry or has no safe ground.",
    )


def validate_walk(asset, variant, spaces=None):
    try:
        document = json.loads(path(asset.blob).read_text())
    except (ValueError, UnicodeError):
        require(False, "invalid_walk_region", "Invalid walk-region JSON.")
    validate_schema(document, WALK)
    unique(document["regions"])
    for region in document["regions"]:
        require(
            region["space_id"] in variant["space_ids"],
            "scope_violation",
            "Walk region is outside the variant.",
        )
        if spaces is not None:
            floors = {s["id"]: s["floor_id"] for s in spaces}
            require(
                region["floor_id"] == floors.get(region["space_id"]),
                "invalid_walk_region",
                "Walk region floor must match its mapped space.",
            )
        polygon = region["polygon_xz"]
        crosses = []
        for i, b in enumerate(polygon):
            a, c = polygon[i - 1], polygon[(i + 1) % len(polygon)]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            require(
                abs(cross) > 1e-6,
                "invalid_walk_region",
                "Walk polygons must be strictly convex.",
            )
            crosses.append(cross)
        require(
            all(x > 0 for x in crosses) or all(x < 0 for x in crosses),
            "invalid_walk_region",
            "Split concave walk areas into convex regions.",
        )
        direction = 1 if crosses[0] > 0 else -1
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            require(
                all(
                    direction
                    * ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
                    >= -1e-6
                    for c in polygon
                ),
                "invalid_walk_region",
                "Walk polygons must be convex and cannot self-intersect.",
            )

    def contains(region, point):
        x, y, z = point
        if abs(y - region["floor_y"]) > 0.05:
            return False
        distances = []
        p = region["polygon_xz"]
        for a, b in zip(p, p[1:] + p[:1]):
            dx, dz = b[0] - a[0], b[1] - a[1]
            distances.append((dx * (z - a[1]) - dz * (x - a[0])) / math.hypot(dx, dz))
        return all(d >= 0.27 for d in distances) or all(d <= -0.27 for d in distances)

    for spawn in variant["spawns"]:
        require(
            any(
                r["floor_id"] == spawn["floor_id"]
                and r["space_id"] == spawn["space_id"]
                and contains(r, spawn["foot_position_m"])
                for r in document["regions"]
            ),
            "invalid_spawn",
            "Spawn capsule must fit inside its walk region.",
        )
    return copy.deepcopy(document)
