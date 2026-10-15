"""Executable JSON Schema contracts. Exported by export_virtual_tour_contracts."""

from jsonschema import Draft202012Validator, FormatChecker
from .errors import TourError, require


def obj(properties, required=None):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties) if required is None else required,
    }


def array(items, minimum=0, maximum=200):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


ID = {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,80}$"}
UUID = {"type": "string", "format": "uuid"}
TEXT = {"type": "string", "minLength": 1, "maxLength": 160}
LABEL = obj({"ar": TEXT, "en": TEXT})
NUMBER = {"type": "number", "minimum": -10000, "maximum": 10000}
YAW = {"type": "number", "minimum": -3.141593, "maximum": 3.141593}
PITCH = {"type": "number", "minimum": -1.570797, "maximum": 1.570797}
VIEW = obj(
    {
        "yaw_rad": YAW,
        "pitch_rad": PITCH,
        "hfov_rad": {"type": "number", "minimum": 0.3, "maximum": 2.1},
    }
)
SPACE = obj(
    {
        "id": ID,
        "label": LABEL,
        "floor_id": ID,
        "space_kind": {"enum": ["room", "bed", "shared", "corridor", "entrance"]},
        "room_id": UUID,
        "bed_id": UUID,
    },
    ["id", "label", "floor_id", "space_kind"],
)
SCENE = obj({"id": ID, "space_id": ID, "source_asset_id": UUID, "initial_view": VIEW})
HOTSPOT = obj(
    {
        "id": ID,
        "source_scene_id": ID,
        "target_scene_id": ID,
        "yaw_rad": YAW,
        "pitch_rad": PITCH,
        "label": LABEL,
        "target_view": VIEW,
    }
)
SPAWN = obj(
    {
        "id": ID,
        "space_id": ID,
        "floor_id": ID,
        "foot_position_m": {
            "type": "array",
            "items": NUMBER,
            "minItems": 3,
            "maxItems": 3,
        },
        "yaw_rad": YAW,
        "pitch_rad": PITCH,
    }
)
CONTEXT = {"anyOf": [{"const": "overview"}, UUID]}
PANO_VARIANT = obj(
    {
        "context": CONTEXT,
        "space_ids": array(ID, 1, 100),
        "scene_ids": array(ID, 2, 40),
        "start_scene_id": ID,
    }
)
MODEL_VARIANT = obj(
    {
        "context": CONTEXT,
        "space_ids": array(ID, 1, 100),
        "visual_asset_id": UUID,
        "collision_asset_id": UUID,
        "walk_asset_id": UUID,
        "spawns": array(SPAWN, 1, 100),
        "start_spawn_id": ID,
    }
)
COMMON = {
    "schema_version": {"const": 1},
    "title": LABEL,
    "captured_at": {"type": "string", "format": "date"},
    "content_origin": {
        "enum": [
            "photographic_capture",
            "reality_scan",
            "measured_model",
            "representative_model",
        ]
    },
    "spaces": array(SPACE, 1, 100),
}
AUTHORING = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        obj(
            {
                **COMMON,
                "kind": {"const": "panorama_360"},
                "scenes": array(SCENE, 2, 40),
                "hotspots": array(HOTSPOT, 2, 400),
                "variants": array(PANO_VARIANT, 1, 50),
            }
        ),
        obj(
            {
                **COMMON,
                "kind": {"const": "model_3d"},
                "coordinate_system": {"const": "right_handed_y_up_meters"},
                "variants": array(MODEL_VARIANT, 1, 50),
            }
        ),
    ],
}
# The first release accepts convex, horizontal walk regions. Concave rooms must
# be split into convex regions. Boundary walls are derived in the viewer.
WALK = obj(
    {
        "schema_version": {"const": 1},
        "regions": array(
            obj(
                {
                    "id": ID,
                    "floor_id": ID,
                    "space_id": ID,
                    "floor_y": NUMBER,
                    "polygon_xz": array(
                        {
                            "type": "array",
                            "items": NUMBER,
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        3,
                        64,
                    ),
                }
            ),
            1,
            100,
        ),
    }
)


def validate_schema(value, schema=AUTHORING):
    error = next(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        None,
    )
    if error:
        path = ".".join(str(p) for p in error.absolute_path) or "document"
        raise TourError("invalid_manifest", f"Invalid {path}: {error.message[:350]}")


def unique(items, key="id"):
    require(
        len({v[key] for v in items}) == len(items),
        "duplicate_identity",
        f"Duplicate {key} in authoring document.",
    )


def connected(scenes, hotspots, start):
    ids = {s["id"] for s in scenes}
    require(
        start in ids and 2 <= len(ids) <= 40,
        "invalid_scene_graph",
        "A tour needs 2–40 scenes and a valid start.",
    )
    links = {s: set() for s in ids}
    for h in hotspots:
        a, b = h["source_scene_id"], h["target_scene_id"]
        require(
            a in ids and b in ids and a != b,
            "invalid_hotspot",
            "Hotspots must connect two scenes in this package.",
        )
        links[a].add(b)

    def reachable(root):
        seen, todo = set(), [root]
        while todo:
            item = todo.pop()
            if item not in seen:
                seen.add(item)
                todo.extend(links[item] - seen)
        return seen

    require(
        all(reachable(s) == ids for s in ids),
        "disconnected_tour",
        "Every scene must be reachable, with a return route.",
    )
