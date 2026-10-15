"""Generate small, explicitly synthetic fixtures. Never seed a public listing.

Run with the backend virtualenv: python tools/virtual_tours/generate_calibration.py /tmp/tour-calibration
"""

import json
import struct
import sys
from pathlib import Path
from PIL import Image, ImageDraw


def box(center, half):
    x, y, z = center
    a, b, c = half
    positions = [
        x - a,
        y - b,
        z - c,
        x + a,
        y - b,
        z - c,
        x + a,
        y + b,
        z - c,
        x - a,
        y + b,
        z - c,
        x - a,
        y - b,
        z + c,
        x + a,
        y - b,
        z + c,
        x + a,
        y + b,
        z + c,
        x - a,
        y + b,
        z + c,
    ]
    indices = [
        0,
        2,
        1,
        0,
        3,
        2,
        4,
        5,
        6,
        4,
        6,
        7,
        0,
        4,
        7,
        0,
        7,
        3,
        1,
        2,
        6,
        1,
        6,
        5,
        0,
        1,
        5,
        0,
        5,
        4,
        3,
        7,
        6,
        3,
        6,
        2,
    ]
    return positions, indices


def model():
    positions, indices = [], []
    # Floor, outer walls, and an internal wall with a 1.6m doorway.
    boxes = [
        ((0, -0.1, 0), (4, 0.1, 4)),
        ((-4, 1.5, 0), (0.05, 1.5, 4)),
        ((4, 1.5, 0), (0.05, 1.5, 4)),
        ((0, 1.5, -4), (4, 1.5, 0.05)),
        ((0, 1.5, 4), (4, 1.5, 0.05)),
        ((-2.4, 1.5, 0), (1.6, 1.5, 0.05)),
        ((2.4, 1.5, 0), (1.6, 1.5, 0.05)),
    ]
    for center, half in boxes:
        vertices, faces = box(center, half)
        offset = len(positions) // 3
        positions.extend(vertices)
        indices.extend(offset + i for i in faces)
    vertex_bytes = struct.pack(f"<{len(positions)}f", *positions)
    index_bytes = struct.pack(f"<{len(indices)}I", *indices)
    binary = vertex_bytes + index_bytes
    doc = {
        "asset": {
            "version": "2.0",
            "generator": "Sokoun SYNTHETIC calibration interior",
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteLength": len(vertex_bytes), "target": 34962},
            {
                "buffer": 0,
                "byteOffset": len(vertex_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(positions) // 3,
                "type": "VEC3",
                "min": [min(positions[i::3]) for i in range(3)],
                "max": [max(positions[i::3]) for i in range(3)],
            },
            {
                "bufferView": 1,
                "componentType": 5125,
                "count": len(indices),
                "type": "SCALAR",
            },
        ],
    }
    encoded = json.dumps(doc, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    return (
        struct.pack("<III", 0x46546C67, 2, 28 + len(encoded) + len(binary))
        + struct.pack("<II", len(encoded), 0x4E4F534A)
        + encoded
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


def generate(directory):
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for i, color in enumerate(((24, 107, 82), (90, 66, 130))):
        image = Image.new("RGB", (4096, 2048), color)
        draw = ImageDraw.Draw(image)
        for x in range(0, 4096, 256):
            draw.line((x, 0, x, 2048), fill="white", width=3)
        for y in range(0, 2048, 256):
            draw.line((0, y, 4096, y), fill="white", width=3)
        for x, direction in (
            (20, "BACK"),
            (1024, "LEFT"),
            (2048, "FRONT"),
            (3072, "RIGHT"),
        ):
            draw.text(
                (x + 20, 1000),
                f"SYNTHETIC TEST {i+1} - NOT A PROPERTY - {direction}",
                fill="yellow",
                font_size=24,
            )
        image.save(target / f"panorama-{i+1}.jpg", quality=85)
    for name in ("visual.glb", "collision.glb"):
        (target / name).write_bytes(model())
    walk = {
        "schema_version": 1,
        "regions": [
            {
                "id": "hall",
                "space_id": "hall",
                "floor_id": "g",
                "floor_y": 0,
                "polygon_xz": [[-3.9, -3.9], [3.9, -3.9], [3.9, 3.9], [-3.9, 3.9]],
            }
        ],
    }
    config = {
        "spaces": [
            {
                "id": "hall",
                "label": {"en": "SYNTHETIC calibration", "ar": "اختبار اصطناعي"},
                "floor_id": "g",
                "space_kind": "shared",
            }
        ],
        "spawns": [
            {
                "id": "entrance",
                "space_id": "hall",
                "floor_id": "g",
                "foot_position_m": [0, 0, 2],
                "yaw_rad": 0,
                "pitch_rad": 0,
            },
            {
                "id": "far-room",
                "space_id": "hall",
                "floor_id": "g",
                "foot_position_m": [0, 0, -2],
                "yaw_rad": 3.14159,
                "pitch_rad": 0,
            },
        ],
        "start_spawn_id": "entrance",
    }
    for name, doc in (("walk.json", walk), ("configuration.json", config)):
        (target / name).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    (target / "README.txt").write_text(
        "SYNTHETIC CALIBRATION ONLY. Not an actual property. Never approve or publish these assets on a real listing.\n"
    )


if __name__ == "__main__":
    generate(sys.argv[1])
