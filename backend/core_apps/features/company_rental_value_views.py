"""Small request/response adapters for company rental value workflows."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .company_views import mutate
from .company_serializers import CommandBody, StrictBody
from .rental_lifecycle_views.common import validated
from .services.company.access import company_for, request_for
from .services.company import bookings, discovery, sourcing, staff_import
from .services.company.read_snapshot import consistent_read


class PreviewThrottle(UserRateThrottle):
    scope = "company_rental_preview"
    rate = "30/min"


class AssistanceBody(CommandBody):
    reason = serializers.CharField(max_length=4000)


class ImportPreviewBody(StrictBody):
    csv_text = serializers.CharField(max_length=200_000, trim_whitespace=False)


def private_response(data):
    response = Response(data)
    response["Cache-Control"] = "private, no-store"
    return response


class CatalogView(FeatureAPIView):
    name = "Catalog"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_rental_value_views",
            "catalog",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        return private_response(
            {"requirements": discovery.requirement_catalog(request.LANGUAGE_CODE)}
        )


# Stable callable import for integrations; URLs use the explicit class.
catalog = CatalogView.as_view()


class AssistanceView(FeatureAPIView):
    name = "Assistance"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_rental_value_views",
            "assistance",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, request_id):
        body = validated(AssistanceBody, request.data)
        return mutate(
            request,
            "company.sourcing.request",
            lambda: request_for(request.user, request_id, lock=True),
            lambda requirement: sourcing.open_request(request.user, requirement, body),
            lambda requirement: bookings.request_payload(requirement, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
assistance = AssistanceView.as_view()


class ImportPreviewView(FeatureAPIView):
    name = "Import Preview"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [PreviewThrottle]
    action_policies = {
        "post": ActionPolicy(
            "company_rental_value_views",
            "import_preview",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id):
        company = company_for(request.user, company_id, "admin")
        body = validated(ImportPreviewBody, request.data)
        return private_response(staff_import.preview(company, body["csv_text"]))


# Stable callable import for integrations; URLs use the explicit class.
import_preview = ImportPreviewView.as_view()


class RentalSummaryView(FeatureAPIView):
    name = "Rental Summary"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_rental_value_views",
            "rental_summary",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        from .services.company import rental_summary as summary

        with consistent_read():
            result = summary.payload(
                request.user, company_for(request.user, company_id)
            )
        return private_response(result)


# Stable callable import for integrations; URLs use the explicit class.
rental_summary = RentalSummaryView.as_view()


class HousingReportView(FeatureAPIView):
    name = "Housing Report"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [PreviewThrottle]
    action_policies = {
        "get": ActionPolicy(
            "company_rental_value_views",
            "housing_report",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        from django.http import HttpResponse
        from .services.company import housing_report as reporting

        with consistent_read():
            company = company_for(request.user, company_id)
            report = reporting.payload(request.user, company, request.query_params)
        if request.query_params.get("export") == "csv":
            response = HttpResponse(
                reporting.csv_bytes(report), content_type="text/csv; charset=utf-8"
            )
            response["Content-Disposition"] = (
                'attachment; filename="company-housing-statement.csv"'
            )
            response["Cache-Control"] = "private, no-store"
            response["X-Content-Type-Options"] = "nosniff"
            return response
        return private_response(report)


# Stable callable import for integrations; URLs use the explicit class.
housing_report = HousingReportView.as_view()
