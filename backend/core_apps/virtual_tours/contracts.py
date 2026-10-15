"""Versioned delivery and bridge contracts, shared with the static viewer build."""

from .schemas import COMMON, HOTSPOT, ID, SPAWN, UUID, VIEW, WALK, array, obj

MOVEMENT = {
    "capsule_height_m": 1.75,
    "capsule_radius_m": 0.25,
    "eye_height_m": 1.60,
    "speed_m_s": 1.20,
    "offset_m": 0.02,
    "fixed_step_s": 1 / 60,
    "max_substeps": 4,
    "stairs_enabled": False,
    "jump_enabled": False,
}
BASE = {
    **COMMON,
    "revision_id": UUID,
    "variant_id": UUID,
    "session_id": UUID,
    "scope_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
}
RESOURCE = obj(
    {
        "resource_id": ID,
        "bytes": {"type": "integer", "minimum": 1, "maximum": 12 * 1024**2},
    }
)
DELIVERY = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        obj(
            {
                **BASE,
                "kind": {"const": "panorama_360"},
                "start_scene_id": ID,
                "scenes": array(
                    obj(
                        {
                            "id": ID,
                            "space_id": ID,
                            "initial_view": VIEW,
                            "projection": {"const": "cubemap"},
                            "tile_set_resource_id": ID,
                            "faces": {"const": ["f", "b", "l", "r", "u", "d"]},
                            "levels": {
                                "const": [
                                    {"size": n, "tile_size": 512}
                                    for n in (512, 1024, 2048)
                                ]
                            },
                        }
                    ),
                    2,
                    40,
                ),
                "hotspots": array(HOTSPOT, 2, 400),
            }
        ),
        obj(
            {
                **BASE,
                "kind": {"const": "model_3d"},
                "coordinate_system": {"const": "right_handed_y_up_meters"},
                "visual": RESOURCE,
                "collision": RESOURCE,
                "walk": RESOURCE,
                "spawns": array(SPAWN, 1, 100),
                "start_spawn_id": ID,
                "movement": {"const": MOVEMENT},
                "camera": {
                    "const": {"vertical_fov_deg": 65, "near_m": 0.05, "far_m": 100}
                },
                "interaction": {
                    "const": {
                        "free_fly": False,
                        "floor_transition": "approved_spawn_only",
                    }
                },
            }
        ),
    ],
}

COMMANDS = {
    "initialize": obj(
        {
            "bootstrap_token": {"type": "string", "minLength": 20, "maxLength": 100},
            "session_id": UUID,
            "language": {"enum": ["ar", "en"]},
            "reduced_motion": {"type": "boolean"},
        }
    ),
    "selectPlace": obj({"place_id": ID}),
    **{
        name: obj({})
        for name in ("resetView", "pause", "resume", "dispose", "readView")
    },
}
BRIDGE_COMMAND = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        obj(
            {
                "protocol_version": {"const": 1},
                "type": {"const": name},
                "message_id": ID,
                "viewer_instance_id": ID,
                "session_id": UUID,
                "payload": payload,
            }
        )
        for name, payload in COMMANDS.items()
    ],
}
WALK_DELIVERY = {"$schema": "https://json-schema.org/draft/2020-12/schema", **WALK}
