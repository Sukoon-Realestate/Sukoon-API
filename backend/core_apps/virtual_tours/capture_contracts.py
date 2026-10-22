"""Additive capture delivery contract. Version 1 packages remain unchanged."""

from .schemas import COMMON, CONTEXT, HOTSPOT, ID, LABEL, NUMBER, UUID, VIEW, array, obj
from .contracts import BASE

MATRIX = array(NUMBER, 16, 16)
RESOURCE = obj({
    "resource_id": ID,
    "bytes": {"type": "integer", "minimum": 1, "maximum": 32 * 1024**2},
    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
})
CAPTURE_AUTHORING = obj({
    **COMMON, "schema_version": {"const": 2},
    "representation": {"const": "capture_derived"},
    "kind": {"enum": ["panorama_360", "model_3d"]},
    "component_ids": array(UUID, 0, 8), "station_ids": array(UUID, 0, 40),
    "variants": array(obj({"context": CONTEXT, "space_ids": array(ID, 1, 40),
                           "component_ids": array(UUID, 0, 8), "station_ids": array(UUID, 0, 40),
                           "start_place_id": UUID}), 1, 40),
    "hotspots": array(HOTSPOT, 0, 400),
})
CAMERA = obj({"id": UUID, "space_id": ID, "matrix": MATRIX})
COMPONENT = obj({
    "id": UUID, "space_ids": array(ID, 1, 40), "label": LABEL,
    "preview": RESOURCE, "detail": RESOURCE,
    "preview_gaussians": {"type": "integer", "minimum": 1, "maximum": 20000},
    "detail_gaussians": {"type": "integer", "minimum": 1, "maximum": 120000},
    "cameras": array(CAMERA, 1, 300), "default_camera_id": UUID,
    "navigation": RESOURCE, "navigation_status": {"enum": ["validated", "needsReview"]},
    "scale_status": {"enum": ["metric", "unverified"]},
})
STATION = obj({"id": UUID, "space_id": ID, "image": RESOURCE,
               "width": {"type": "integer", "minimum": 2048, "maximum": 4096},
               "height": {"type": "integer", "minimum": 1024, "maximum": 2048},
               "full_sphere": {"const": True}, "initial_view": VIEW})
CAPTURE_DELIVERY = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **obj({**BASE, "schema_version": {"const": 2},
           "representation": {"const": "gaussian_capture"},
           "kind": {"enum": ["panorama_360", "model_3d"]},
           "components": array(COMPONENT, 0, 8), "stations": array(STATION, 0, 40),
           "alignments": array(obj({"station_id": UUID, "component_id": UUID,
                                    "matrix": MATRIX}), 0, 320),
           "hotspots": array(HOTSPOT, 0, 400), "start_place_id": UUID,
           "coordinate_system": {"const": "right_handed_y_up"},
           "free_fly": {"const": False}}),
}
