import re
from django.urls import resolve
from jsonschema import Draft202012Validator
from core_apps.virtual_tours.openapi import document


def test_exported_contracts_and_http_methods_match_registered_routes():
    contract = document()
    for schema in contract["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)
    for path, operations in contract["paths"].items():

        def parameter(match):
            name = match.group(1)
            if name in ("part", "level", "x", "y"):
                return "1"
            if name == "face":
                return "f"
            if name in ("key", "resource_id"):
                return "example01"
            return "00000000-0000-4000-8000-000000000001"

        url = "/api/v1" + re.sub(r"\{(\w+)\}", parameter, path)
        view = resolve(url).func.cls
        actual = set(view.http_method_names) - {"head", "options"}
        assert set(operations) == actual, (url, operations, actual)
