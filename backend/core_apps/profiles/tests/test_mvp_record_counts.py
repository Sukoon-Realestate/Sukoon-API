"""Active request badges count business records, independently of notices."""
from datetime import time, timedelta

import pytest
from django.utils import timezone
from django.urls import reverse

from core_apps.notifications.models import Notification
from core_apps.properties.models import PropertyVisit
from core_apps.properties.tests.conftest import apartment_type, cairo_city, cairo_governorate  # noqa: F401
from core_apps.properties.tests.test_owner_visit_screens import create_property

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('workspace', ['owner', 'individual'])
def test_viewing_badge_counts_records_instead_of_notifications(
    auth_client, user, another_user, apartment_type, cairo_city, cairo_governorate, workspace,
):
    owner, renter = (user, another_user) if workspace == 'owner' else (another_user, user)
    prop = create_property(owner, apartment_type, cairo_city, cairo_governorate)
    PropertyVisit.objects.create(property=prop, tenant=renter,
        visit_date=timezone.localdate() + timedelta(days=2), visit_time=time(12), status='pending')
    for i in range(3):
        Notification.objects.create(user=user, scope=workspace, title=f'Synthetic notice {i}')
    path = reverse('owner-unread-counts' if workspace == 'owner' else 'tenant-unread-counts')
    response = auth_client.get(path)
    assert response.status_code == 200, response.content
    data = response.json()['data']
    assert data['visit_requests_count'] == 1
    assert data['unread_notifications_count'] == 3
    Notification.objects.filter(user=user).update(is_read=True)
    data = auth_client.get(path).json()['data']
    assert data['visit_requests_count'] == 1
    assert data['unread_notifications_count'] == 0
