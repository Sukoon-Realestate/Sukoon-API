"""Bounded identity screen projections with populated related activity."""
from datetime import date, time
import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from core_apps.profiles.services import ProfileService
from core_apps.profiles.serializers import MyAccountScreenSerializer, AccountSummaryScreenSerializer
from core_apps.profiles.tests.test_screen_views import create_test_property
from core_apps.properties.models import PropertyVisit, PropertyVisitReview


@pytest.mark.django_db
@pytest.mark.parametrize("size", [1, 20, 100])
def test_profile_screen_query_budgets(user, another_user, size):
    prop = create_test_property(another_user)
    for index in range(size):
        visit = PropertyVisit.objects.create(
            tenant=user, property=prop, visit_date=date(2026, 7, 20),
            visit_time=time(14, index % 60), status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisitReview.objects.create(
            visit=visit, overall_rating=5, cleanliness_rating=5,
            listing_accuracy_rating=5, owner_interaction_rating=5,
        )
    with CaptureQueriesContext(connection) as queries:
        account = MyAccountScreenSerializer(ProfileService.get_my_account_data(user)).data
    assert len(queries) <= 8
    assert account["stats"]["visits_count"] == account["stats"]["reviews_count"] == size
    assert len(json.dumps(account, default=str).encode()) < 8192
    with CaptureQueriesContext(connection) as queries:
        summary = AccountSummaryScreenSerializer(ProfileService.get_account_summary_data(user)).data
    assert len(queries) <= 6
    assert len(json.dumps(summary, default=str).encode()) < 8192
