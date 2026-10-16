"""Generate an additive OpenAPI slice from the actual strict DRF input serializers."""

import json, os, sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--contract", required=True)
parser.add_argument("--output", default="docs/rental_gap_closure/openapi.json")
args = parser.parse_args()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
import django

django.setup()
from rest_framework.schemas.openapi import AutoSchema
from core_apps.features import rental_lifecycle_serializers as serializers
from core_apps.features.pagination import FeaturePagination

schema = AutoSchema()
requests = {
    name: schema.map_serializer(getattr(serializers, name)())
    for name in [
        "CommandBody",
        "ProfileBody",
        "ShareReviewBody",
        "ShareBody",
        "HoldBody",
        "ReasonBody",
        "ConfirmationBody",
        "FactBody",
        "CaseBody",
        "CaseActionBody",
        "ClaimBody",
        "BookingBody",
        "ConsentBody",
        "AnswerBody",
    ]
}
for value in requests.values():
    value["additionalProperties"] = False
responses = json.loads(Path(args.contract).read_text())["responses"]


def shape(v):
    if isinstance(v, bool):
        return {"type": "boolean"}
    if isinstance(v, int):
        return {"type": "integer"}
    if isinstance(v, str):
        return {"type": "string"}
    if v is None:
        return {"nullable": True}
    if isinstance(v, list):
        return {"type": "array", "items": shape(v[0]) if v else {}}
    return {
        "type": "object",
        "properties": {k: shape(value) for k, value in v.items()},
        "required": list(v),
    }


for key, value in responses.items():
    requests[key.title() + "Response"] = shape(value)
requests["Envelope"] = {
    "type": "object",
    "required": ["message", "data"],
    "additionalProperties": False,
    "properties": {"message": {"type": "string"}, "data": {}},
}
requests["MutationReceipt"] = {
    "type": "object",
    "required": ["resource", "operation_receipt"],
    "properties": {
        "resource": {"type": "object"},
        "operation_receipt": {
            "type": "object",
            "required": ["id", "subject_id", "request_key", "revision", "status"],
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "subject_id": {"type": "string", "format": "uuid"},
                "request_key": {"type": "string", "format": "uuid"},
                "revision": {"type": "integer", "minimum": 1},
                "status": {"enum": ["confirmed"]},
            },
        },
    },
}
items = [
    ("application-profile/", {"get": None, "patch": "ProfileBody"}),
    ("application-profile/versions/", {"post": "CommandBody"}),
    ("application-profile/versions/{version_id}/", {"get": None}),
    ("application-shares/preview/", {"post": "ShareReviewBody"}),
    ("application-shares/", {"get": None, "post": "ShareBody"}),
    ("application-shares/{share_id}/", {"get": None, "post": "CommandBody"}),
    ("application-shares/{share_id}/revoke/", {"post": "CommandBody"}),
    ("properties/{property_id}/decision-summary/", {"get": None}),
    ("properties/{property_id}/decision-facts/", {"post": "FactBody"}),
    (
        "properties/{property_id}/availability-confirmation/",
        {"post": "ConfirmationBody"},
    ),
    ("availability-blocks/", {"get": None, "post": "HoldBody"}),
    ("reservation-holds/", {"get": None, "post": "HoldBody"}),
    ("reservation-holds/{hold_id}/", {"get": None}),
    ("reservation-holds/{hold_id}/extend/", {"post": "ReasonBody"}),
    ("reservation-holds/{hold_id}/release/", {"post": "ReasonBody"}),
    ("deals/{subject_id}/", {"get": None}),
    ("owner-application-queue/", {"get": None}),
    ("rental-cases/", {"get": None, "post": "CaseBody"}),
    ("move-in-cases/", {"get": None, "post": "CaseBody"}),
    ("rental-cases/{case_id}/", {"get": None}),
    ("rental-cases/{case_id}/actions/", {"post": "CaseActionBody"}),
    ("operations/rental-cases/", {"get": None, "post": "CaseBody"}),
    ("operations/rental-cases/{case_id}/actions/", {"post": "CaseActionBody"}),
    ("operations/verification-claims/", {"post": "ClaimBody"}),
    ("operations/verification-claims/{claim_id}/revoke/", {"post": "ReasonBody"}),
    ("group-booking-proposals/", {"get": None, "post": "BookingBody"}),
    ("group-booking-proposals/{booking_id}/", {"get": None}),
    ("group-booking-proposals/{booking_id}/submit/", {"post": "CommandBody"}),
    ("group-booking-proposals/{booking_id}/consents/", {"post": "ConsentBody"}),
    ("group-booking-proposals/{booking_id}/withdraw/", {"post": "CommandBody"}),
    ("terms-proposals/{proposal_id}/propose-answer/", {"post": "AnswerBody"}),
]
import re

paths = {}
listpaths = {
    "application-shares/",
    "reservation-holds/",
    "availability-blocks/",
    "rental-cases/",
    "move-in-cases/",
    "operations/rental-cases/",
    "group-booking-proposals/",
    "owner-application-queue/",
}
for path, methods in items:
    operations = {}
    for method, request in methods.items():
        action = {
            "operationId": method
            + "_"
            + re.sub(r"[^a-z_]+", "_", path.replace("/", "_")).strip("_"),
            "tags": ["rental-lifecycle"],
            "parameters": [
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
                for name in re.findall(r"{(.*?)}", path)
            ],
            "responses": {
                code: {
                    "description": desc,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Envelope"}
                        }
                    },
                }
                for code, desc in [
                    ("200", "Read or confirmed mutation"),
                    ("400", "Invalid fields or unsupported input"),
                    ("401", "Authentication required"),
                    ("403", "Actor role or capability unavailable"),
                    ("404", "Subject inaccessible"),
                    (
                        "409",
                        "Revision, consent, policy, inventory or reconciliation conflict",
                    ),
                ]
            },
        }
        if request:
            action["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/" + request}
                    }
                },
            }
        if (
            method == "post"
            and path.endswith(("/",))
            and path
            in {
                "application-profile/versions/",
                "application-shares/",
                "reservation-holds/",
                "availability-blocks/",
                "rental-cases/",
                "group-booking-proposals/",
                "operations/verification-claims/",
            }
        ):
            action["responses"]["201"] = {
                "description": "Created with canonical operation receipt",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Envelope"}
                    }
                },
            }
        if path in listpaths and method == "get":
            action["parameters"] += [
                {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer", "minimum": 1},
                }
            ]
            action["responses"]["200"][
                "description"
            ] = "Existing pagination: data is a list; X-Page, X-Per-Page, X-Total-Count and X-Total-Pages headers, with X-Next-Page and X-Previous-Page when present."
        if path.endswith("decision-summary/"):
            action["parameters"] += [
                {
                    "name": "offer_id",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "name": "offer_revision",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "integer", "minimum": 1},
                },
            ] + [
                {
                    "name": n,
                    "in": "query",
                    "schema": {"type": "string", "format": "date"},
                }
                for n in ["starts_on", "ends_on_exclusive"]
            ]
        operations[method] = action
    paths["/" + path] = operations
output = {
    "openapi": "3.0.3",
    "info": {
        "title": "Sokoun rental lifecycle gap closure additive contract",
        "version": "2026-10-15",
        "description": "Strict request schemas generated from DRF. Example response shapes derive from local test HTTP responses and do not prove production readiness. See API_CONTRACT.md for authorization, receipt and projection rules.",
    },
    "servers": [{"url": "/api/v1/features/v1"}],
    "security": [{"bearerAuth": []}],
    "paths": paths,
    "components": {
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        },
        "schemas": requests,
    },
}
for outputpath in [Path(args.output)]:
    outputpath.parent.mkdir(parents=True, exist_ok=True)
    outputpath.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(f"{len(paths)} paths; {len(requests)} schemas")
