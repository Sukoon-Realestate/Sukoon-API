"""Exportable OpenAPI 3.1 contract for the isolated tour API surface."""

import re
from copy import deepcopy
from .contracts import DELIVERY, BRIDGE_COMMAND, WALK_DELIVERY
from .schemas import AUTHORING, ID, UUID, array, obj
from .uploads import ROLES

STRING = {"type": "string"}
BOOL = {"type": "boolean"}
INTEGER = {"type": "integer", "minimum": 0}
HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}


def ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


ASSET = obj(
    {
        "id": UUID,
        "role": {"enum": list(ROLES)},
        "sha256": HASH,
        "size": INTEGER,
        "media_type": STRING,
    }
)
REVISION = obj(
    {
        "id": UUID,
        "tour_id": UUID,
        "draft_version": INTEGER,
        "etag": STRING,
        "authoring": {"oneOf": [ref("Authoring"), obj({})]},
        "processing_state": {
            "enum": ["draft", "queued", "processing", "ready", "failed"]
        },
        "review_state": {"enum": ["not_submitted", "pending", "approved", "rejected"]},
        "source_hash": STRING,
        "stage": STRING,
        "report": {"type": "object"},
        "assets": array(ref("Asset"), 0, 2000),
        "variants": array(
            obj({"id": UUID, "context": STRING, "scope_fingerprint": HASH}), 0, 50
        ),
        "operation_id": UUID,
    },
    [
        "id",
        "tour_id",
        "draft_version",
        "etag",
        "authoring",
        "processing_state",
        "review_state",
        "source_hash",
        "stage",
        "report",
        "assets",
        "variants",
    ],
)
TOUR = obj(
    {
        "id": UUID,
        "property_id": {"anyOf": [UUID, {"type": "null"}]},
        "asset_id": UUID,
        "asset_kind": {"enum": ["property", "building", "complex"]},
        "kind": {"enum": ["panorama_360", "model_3d"]},
        "disabled": BOOL,
        "deleted": BOOL,
        "active_revision_id": {"anyOf": [UUID, {"type": "null"}]},
        "latest_revision": {"anyOf": [ref("Revision"), {"type": "null"}]},
        "operation_id": UUID,
    },
    [
        "id",
        "property_id",
        "asset_id",
        "asset_kind",
        "kind",
        "disabled",
        "deleted",
        "active_revision_id",
        "latest_revision",
    ],
)
UPLOAD = obj(
    {
        "id": UUID,
        "state": {"enum": ["open", "complete", "aborted", "expired"]},
        "size": INTEGER,
        "sha256": HASH,
        "role": {"enum": list(ROLES)},
        "part_bytes": {"const": 8388608},
        "received_parts": array({"type": "integer", "minimum": 1}, 0, 32),
        "asset_id": {"anyOf": [UUID, {"type": "null"}]},
        "expires_at": STRING,
        "operation_id": UUID,
    },
    [
        "id",
        "state",
        "size",
        "sha256",
        "role",
        "part_bytes",
        "received_parts",
        "asset_id",
        "expires_at",
    ],
)


def document():
    schemas = {
        "Authoring": AUTHORING,
        "Delivery": DELIVERY,
        "WalkRegions": WALK_DELIVERY,
        "BridgeCommand": BRIDGE_COMMAND,
        "Asset": ASSET,
        "Revision": REVISION,
        "Tour": TOUR,
        "Upload": UPLOAD,
        "Error": obj({"message": STRING, "data": {"type": "null"}}),
        "Operation": obj(
            {
                "id": UUID,
                "key": STRING,
                "action": STRING,
                "resource": STRING,
                "request_hash": HASH,
                "status": {"enum": ["succeeded"]},
                "result": {"type": "object"},
                "http_status": INTEGER,
                "expires_at": STRING,
            }
        ),
        "Bootstrap": obj(
            {
                "session_id": UUID,
                "bootstrap_token": STRING,
                "bootstrap_expires_at": STRING,
                "viewer_url": {"type": "string", "format": "uri"},
                "protocol_version": {"const": 1},
            }
        ),
        "Exchange": obj(
            {"session_id": UUID, "credential": STRING, "expires_at": STRING}
        ),
    }
    paths = {}

    def route(
        path,
        method,
        summary,
        response=None,
        body=None,
        security="account",
        mutation=False,
        etag=False,
        statuses=(200,),
        query=(),
    ):
        parameters = [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": (
                    INTEGER
                    if name in ("part", "level", "x", "y")
                    else STRING if name in ("key", "face", "resource_id") else UUID
                ),
            }
            for name in re.findall(r"\{(\w+)\}", path)
        ]
        if mutation:
            parameters.append(
                {
                    "name": "Idempotency-Key",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "pattern": "^[A-Za-z0-9_-]{8,100}$"},
                    "description": "Persist before sending. Same account/key/body/If-Match replays for 30 days. Keys remain tombstones after expiry.",
                }
            )
        if etag:
            parameters.append(
                {
                    "name": "If-Match",
                    "in": "header",
                    "required": True,
                    "schema": STRING,
                    "example": '"draft-2"',
                    "description": "Exact current draft ETag. A stale version returns 412.",
                }
            )
        parameters.extend(
            {"name": name, "in": "query", "required": name == "grant", "schema": STRING}
            for name in query
        )
        content = {
            "application/json": {
                "schema": obj(
                    {"message": STRING, "data": response or {"type": "object"}}
                )
            }
        }
        value = {
            "summary": summary,
            "operationId": method
            + "_"
            + re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_"),
            "parameters": parameters,
            "security": [] if security == "public" else [{security: []}],
            "responses": {
                str(status): {
                    "description": "Success; Cache-Control: private, no-store.",
                    "content": content,
                }
                for status in statuses
            },
        }
        for status in (400, 401, 403, 404, 409, 410, 412, 413, 422, 429, 503):
            value["responses"][str(status)] = {
                "description": "Rejected. See X-App-Error-Code and message. Refresh/reconcile conflicts; do not replace an ambiguous write key.",
                "headers": {"X-App-Error-Code": {"schema": STRING}},
                "content": {"application/json": {"schema": ref("Error")}},
            }
        if body is not None:
            value["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": body}},
            }
        paths.setdefault(path, {})[method] = value
        return value

    p = "/properties/{property_id}/virtual-tours/"
    t, r = p + "{tour_id}/", p + "{tour_id}/revisions/{revision_id}/"
    u, s = (
        "/virtual-tour-uploads/{upload_id}/",
        "/virtual-tour-viewer/sessions/{session_id}/",
    )
    resource = s + "resources/{resource_id}/"
    route(
        "/properties/virtual-tours/capabilities/",
        "get",
        "Read current per-kind capability flags and limits",
        security="public",
    )
    route(
        p,
        "get",
        "List owner's tours including deleted records",
        obj({"tours": array(ref("Tour"), 0, 2)}),
    )
    route(
        p,
        "post",
        "Create tour after ordinary media succeeds, or restore deleted authoring access",
        ref("Tour"),
        obj({"kind": {"enum": ["panorama_360", "model_3d"]}}),
        mutation=True,
        statuses=(200, 201),
    )
    route(
        p + "available/",
        "get",
        "List approved packages for overview or exact offer; no partial-to-whole fallback",
        security="public",
        query=("offer_id",),
    )
    route(
        t,
        "delete",
        "Soft-delete and revoke public viewing",
        ref("Tour"),
        obj({}),
        mutation=True,
    )
    route(
        t + "unpublish/",
        "post",
        "Disable public viewing immediately",
        ref("Tour"),
        obj({}),
        mutation=True,
    )
    route(
        t + "revisions/",
        "post",
        "Create revision; optionally clone immutable source",
        ref("Revision"),
        obj({"from_revision_id": UUID}, []),
        mutation=True,
        statuses=(201,),
    )
    route(r, "get", "Read revision and ETag", ref("Revision"))
    route(
        r,
        "patch",
        "Replace validated authoring document",
        ref("Revision"),
        obj({"authoring": ref("Authoring")}),
        mutation=True,
        etag=True,
    )
    route(
        r + "process/",
        "post",
        "Queue immutable package processing",
        ref("Revision"),
        obj({}),
        mutation=True,
        etag=True,
        statuses=(200, 202),
    )
    route(
        r + "submit-review/",
        "post",
        "Freeze ready revision for privacy review",
        ref("Revision"),
        obj({"source_hash": HASH}),
        mutation=True,
        etag=True,
    )
    route(
        r + "uploads/",
        "post",
        "Start resumable private asset upload",
        ref("Upload"),
        obj(
            {
                "role": {"enum": list(ROLES)},
                "size": {"type": "integer", "minimum": 1, "maximum": 262144000},
                "sha256": HASH,
                "media_type": STRING,
            }
        ),
        mutation=True,
        etag=True,
        statuses=(201,),
    )
    route(u, "get", "Reconcile received parts and completed asset", ref("Upload"))
    route(
        u, "delete", "Abort an unfinished upload", ref("Upload"), obj({}), mutation=True
    )
    route(
        u + "parts/",
        "post",
        "Issue five-minute scoped part PUT grant",
        body=obj({"part_number": {"type": "integer", "minimum": 1, "maximum": 32}}),
    )
    raw = route(
        u + "parts/{part}/",
        "put",
        "Upload exactly the expected 8 MiB part, final part may be smaller",
        ref("Upload"),
        security="public",
        query=("grant",),
    )
    raw["requestBody"] = {
        "required": True,
        "content": {
            "application/octet-stream": {
                "schema": {"type": "string", "format": "binary"}
            }
        },
    }
    route(
        u + "complete/",
        "post",
        "Verify whole-file SHA-256 and seal a new immutable blob",
        ref("Upload"),
        obj({}),
        mutation=True,
    )
    for suffix in ("{operation_id}/", "by-key/{key}/"):
        route(
            "/virtual-tour-operations/" + suffix,
            "get",
            "Read own operation receipt; expired receipts return 410",
            ref("Operation"),
        )
    route(
        t + "viewer-sessions/",
        "post",
        "Create single-use 60-second bootstrap; preview requires owner or reviewer",
        ref("Bootstrap"),
        obj(
            {"offer_id": UUID, "preview": BOOL, "revision_id": UUID, "context": STRING},
            [],
        ),
        security="public",
        statuses=(201,),
    )
    route(
        "/virtual-tour-viewer/exchange/",
        "post",
        "Exchange bootstrap once for 15-minute read credential",
        ref("Exchange"),
        obj({"bootstrap_token": STRING}),
        security="public",
    )
    route(
        s + "manifest/",
        "get",
        "Read exact scoped immutable delivery document",
        ref("Delivery"),
        security="viewer",
    )
    route(
        s + "renew/",
        "post",
        "Revalidate scope and extend session to 15 minutes",
        body=obj({}),
        security="viewer",
    )
    route(s, "delete", "Revoke session", body=obj({}), security="viewer")
    route(
        resource + "access/",
        "get",
        "Issue resource-only 120-second byte grant",
        security="viewer",
    )
    for suffix in ("bytes/", "bytes/{face}/{level}/{x}/{y}/"):
        raw = route(
            resource + suffix,
            "get",
            "Read private asset after current publication and inventory checks",
            security="public",
            query=("grant",),
        )
        raw["responses"]["200"]["content"] = {
            "application/octet-stream": {
                "schema": {"type": "string", "format": "binary"}
            }
        }
    route(
        "/admin" + r + "review-decisions/",
        "post",
        "Staff-only immutable hash-bound approval or rejection",
        ref("Revision"),
        obj(
            {
                "decision": {"enum": ["approved", "rejected"]},
                "expected_source_hash": HASH,
                "reason": {"type": "string", "minLength": 1, "maxLength": 4000},
            }
        ),
        mutation=True,
    )
    # Containers share the canonical tour lifecycle. Keep fixed kind segments
    # aligned with urls.py and preserve the legacy property routes verbatim.
    for kind in ("building", "complex"):
        for path, operations in list(paths.items()):
            if p not in path:
                continue
            target = path.replace(
                p, f"/residential-assets/{kind}/{{property_id}}/virtual-tours/"
            )
            paths[target] = deepcopy(operations)
            for method, operation in paths[target].items():
                operation["operationId"] = (
                    method + "_" + re.sub(r"[^a-zA-Z0-9]+", "_", target).strip("_")
                )
                operation["description"] = (
                    "Common-area overview of this container only. Unit interiors and exact unit offers retain their own tours. property_id in this path identifies the container."
                )
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Sokoun virtual tours",
            "version": "1.0.0",
            "description": "Owner JWT stays in Flutter. Only isolated viewer credentials reach JavaScript. All metadata and bytes require current server policy; signed links are not standalone authorization.",
        },
        "servers": [{"url": "/api/v1"}],
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {
                "account": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                "viewer": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Tour-Credential",
                },
            },
        },
    }
