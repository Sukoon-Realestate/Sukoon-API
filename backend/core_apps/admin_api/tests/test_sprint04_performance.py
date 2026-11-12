"""Sprint 04 prepared projections and query budgets on repeatable fixtures."""

import json
import os
import time
import tracemalloc
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone
from django.test.utils import CaptureQueriesContext

from core_apps.admin_api.models import PushCampaign, CampaignRecipient
from core_apps.admin_api.serializers.property_serializers import (
    AdminPropertyItemSerializer,
)
from core_apps.admin_api.services.analytics_service import get_analytics_stats
from core_apps.admin_api.services.dashboard_service import get_executive_dashboard_stats
from core_apps.admin_api.services.property_service import get_admin_properties_queryset
from core_apps.admin_api.services.system_service_parts.get_system_health import (
    get_push_campaigns,
)
from core_apps.common.models import ContentView
from django.contrib.contenttypes.models import ContentType
from core_apps.properties.models import Property, PropertyType, City, Governorate

pytestmark = pytest.mark.django_db


def measured(name, size, operation):
    tracemalloc.start()
    started = time.perf_counter()
    with CaptureQueriesContext(connection) as queries:
        result = operation()
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    report = dict(
        case=name,
        size=size,
        queries=len(queries),
        seconds=elapsed,
        peak_python_bytes=peak,
        payload_bytes=len(json.dumps(result, default=str).encode()),
    )
    if os.environ.get("SPRINT04_METRICS"):
        with Path(os.environ["SPRINT04_METRICS"]).open("a") as stream:
            stream.write(json.dumps(report) + "\n")
    return result, report


@pytest.mark.parametrize("size", [5, 40, 100])
def test_admin_property_page(size, user):
    region = Governorate.objects.create(name="Budget region")
    city = City.objects.create(name="Budget city", governorate=region)
    kind = PropertyType.objects.create(name="Budget kind", slug="budget-kind")
    rows = Property.objects.bulk_create(
        [
            Property(
                owner=user,
                title=f"Budget {i}",
                governorate=region,
                city=city,
                property_type=kind,
            )
            for i in range(size)
        ]
    )
    ct = ContentType.objects.get_for_model(Property)
    ContentView.objects.bulk_create(
        [
            ContentView(content_type=ct, object_id=row.pkid, last_viewed=timezone.now())
            for row in rows
        ]
    )
    data, report = measured(
        "admin-properties",
        size,
        lambda: list(
            AdminPropertyItemSerializer(
                get_admin_properties_queryset()[:size], many=True
            ).data
        ),
    )
    assert len(data) == size and all(
        row["views"] == 1 and row["imagesCount"] == 0 for row in data
    )
    assert report["queries"] <= 2


@pytest.mark.parametrize("days", [7, 30, 90])
def test_analytics_query_budget(days, user):
    data, report = measured("analytics", days, lambda: get_analytics_stats(days))
    assert len(data["dailyChart"]) == days
    assert report["queries"] <= 18


def test_executive_query_budget(user):
    data, report = measured("executive-dashboard", 30, get_executive_dashboard_stats)
    assert len(data["monthlyUserChartData"]) == 30
    assert report["queries"] <= 22


@pytest.mark.parametrize("size", [1, 10, 100])
def test_campaign_summary_query_budget(size, user):
    for i in range(size):
        campaign = PushCampaign.objects.create(
            creator=user,
            title=f"C {i}",
            body="Body",
            audience="all",
            request_key=uuid4(),
            preview_digest="test",
        )
        CampaignRecipient.objects.create(
            campaign=campaign, user=user, workspace="individual"
        )
    data, report = measured("campaign-history", size, get_push_campaigns)
    assert len(data) == size
    assert all(row["recipientCount"] == row["receiptCount"] == 1 for row in data)
    assert report["queries"] <= 5


@pytest.mark.parametrize("size", [1, 20, 100])
def test_prepared_kyc_and_reports(size, user, another_user):
    from core_apps.admin_api.models import KYCSubmission, UserReport
    from core_apps.admin_api.services.kyc_service import get_kyc_queue_queryset
    from core_apps.admin_api.services.report_service import get_reports_queryset
    from core_apps.admin_api.serializers.kyc_serializers import (
        KYCSubmissionListSerializer,
    )
    from core_apps.admin_api.serializers.report_serializers_parts.support_ticket_serializer import (
        UserReportListSerializer,
    )

    KYCSubmission.objects.bulk_create(
        [KYCSubmission(profile=user.profile) for _ in range(size)]
    )
    UserReport.objects.bulk_create(
        [
            UserReport(reported_user=user, reporter=another_user, reason="Budget")
            for _ in range(size)
        ]
    )
    for name, query, serializer in [
        ("kyc", get_kyc_queue_queryset, KYCSubmissionListSerializer),
        ("reports", get_reports_queryset, UserReportListSerializer),
    ]:
        data, report = measured(
            name, size, lambda: list(serializer(query()[:size], many=True).data)
        )
        assert len(data) == size and report["queries"] <= 1


@pytest.mark.parametrize("size", [1, 25])
@pytest.mark.parametrize(
    "kind", ["cities", "districts", "campuses", "subscription_plans", "plan_benefits"]
)
@pytest.mark.mvp_deferred
def test_content_projection_fetch_plan(kind, size, settings):
    from core_apps.admin_api.services import content_registry as registry
    from core_apps.properties.models import District
    from core_apps.features.student_models import University, Campus

    region = Governorate.objects.create(name="Registry region")
    city = City.objects.create(name="Registry city", governorate=region)
    if kind == "cities":
        City.objects.bulk_create(
            [
                City(name=f"City {i}", slug=f"city-{i}", governorate=region)
                for i in range(size)
            ]
        )
    elif kind == "districts":
        District.objects.bulk_create(
            [District(name=f"District {i}", city=city) for i in range(size)]
        )
    elif kind == "campuses":
        university = University.objects.create(name_ar="جامعة", name_en="University")
        Campus.objects.bulk_create(
            [
                Campus(
                    name_ar=f"حرم {i}",
                    name_en=f"Campus {i}",
                    city=city,
                    university=university,
                )
                for i in range(size)
            ]
        )
    else:
        from core_apps.features.models import (
            SubscriptionPlan,
            CommerceFeature,
            PlanBenefit,
        )

        plans = SubscriptionPlan.objects.bulk_create(
            [
                SubscriptionPlan(
                    name_en=f"Plan {i}",
                    name_ar=f"خطة {i}",
                    workspace="tenant",
                    amount_minor=100,
                )
                for i in range(size)
            ]
        )
        if kind == "plan_benefits":
            feature = CommerceFeature.objects.create(
                code="budget", workspace="tenant", label_en="Budget", label_ar="ميزة"
            )
            PlanBenefit.objects.bulk_create(
                [PlanBenefit(plan=plan, feature=feature) for plan in plans]
            )
    data, report = measured(
        "content-" + kind,
        size,
        lambda: [
            registry.projection(kind, row)
            for row in (
                registry.queryset(kind)
                if hasattr(registry, "queryset")
                else registry.spec(kind).model.objects.all()
            ).order_by("pk")[:size]
        ],
    )
    assert len(data) == size and report["queries"] == 1


def test_campaign_summaries_preserve_deleted_account_and_delivery_totals(user):
    from core_apps.admin_api.models import CampaignDelivery
    from core_apps.admin_api.services.push_campaigns import payload

    item = PushCampaign.objects.create(
        creator=user, title="Totals", body="Body", audience="all", request_key=uuid4()
    )
    first = CampaignRecipient.objects.create(
        campaign=item, user=user, workspace="tenant"
    )
    CampaignRecipient.objects.create(campaign=item, user=user, workspace="owner")
    removed = CampaignRecipient.objects.create(
        campaign=item, user=None, workspace="tenant"
    )
    CampaignDelivery.objects.create(recipient=first, state="accepted_by_provider")
    CampaignDelivery.objects.create(recipient=removed, state="delivery_unknown")
    value = payload(item)
    assert value["recipientCount"] == 2 and value["receiptCount"] == 3
    assert value["workspaceCounts"] == {"tenant": 2, "owner": 1}
    assert value["pushAccountCount"] == 2
    assert value["deliveryCounts"] == {"accepted_by_provider": 1, "delivery_unknown": 1}
    CampaignDelivery.objects.filter(recipient=removed).update(state="skipped")
    assert payload(item)["deliveryCounts"] == {"accepted_by_provider": 1, "skipped": 1}
