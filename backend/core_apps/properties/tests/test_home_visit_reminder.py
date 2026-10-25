from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.features.company_models import Company, CompanyMembership
from core_apps.features.planning_models import HousingGroup, GroupMembership, GroupProcess
from core_apps.properties.models import PropertyVisit
from .test_views import _create_property

pytestmark = pytest.mark.django_db


@pytest.fixture
def appointments(user, another_user):
    prop = _create_property(owner=another_user, title='Reminder property')
    counter = 0

    def create(**kwargs):
        nonlocal counter
        counter += 1
        return PropertyVisit.objects.create(**{
            'property': prop, 'tenant': user, 'visit_date': timezone.localdate(),
            'visit_time': f'{counter:02}:00:00', 'status': PropertyVisit.Status.CONFIRMED,
            **kwargs,
        })
    return create


def read(client, workspace='individual', **kwargs):
    response = client.get(reverse('home-visit-reminder'), {'workspace': workspace, **kwargs})
    assert response.status_code == 200, response.content
    assert response['Cache-Control'] == 'private, no-store'
    return response.json()['data']['banner']


def test_personal_today_nearest_and_cancel_then_future(auth_client, appointments):
    appointments(status='pending')
    appointments(status='rejected')
    appointments(visit_date=timezone.localdate() - timedelta(days=1))
    first = appointments()
    later = appointments(visit_date=timezone.localdate() + timedelta(days=1))
    banner = read(auth_client)
    assert banner['visit_id'] == str(first.id) and banner['is_today'] is True
    first.status = 'canceled'
    first.save()
    banner = read(auth_client)
    assert banner['visit_id'] == str(later.id) and banner['is_today'] is False


def test_student_and_individual_do_not_mix(auth_client, appointments):
    student = appointments(renter_workspace='student')
    personal = appointments()
    assert read(auth_client)['visit_id'] == str(personal.id)
    assert read(auth_client, 'student')['visit_id'] == str(student.id)
    # Keep the original individual home feed scoped as well.
    response = auth_client.get(reverse('property-homepage-list'))
    assert response.json()['data']['banner']['visit_id'] == str(personal.id)


def test_owner_reads_own_received_visits_not_personal_visits(auth_client, user, another_user, appointments):
    appointments()
    own = _create_property(owner=user)
    visit = appointments(property=own, tenant=another_user)
    assert read(auth_client, 'owner')['visit_id'] == str(visit.id)


def company(user, *, coordinator=True):
    value = Company.objects.create(name='Reminder company')
    membership = CompanyMembership.objects.create(company=value, user=user, is_active=True, is_coordinator=coordinator)
    return value, membership


def test_company_scope_and_current_membership(auth_client, user, another_user, appointments):
    first, membership = company(user)
    second, _ = company(user)
    a = appointments(company=first, tenant=another_user, context_kind='company')
    b = appointments(company=second, tenant=another_user, context_kind='company')
    assert read(auth_client, 'company', company_id=first.id)['visit_id'] == str(a.id)
    assert read(auth_client, 'company', company_id=second.id)['visit_id'] == str(b.id)
    assert read(auth_client) is None
    assert read(auth_client, 'student') is None
    membership.is_active = False
    membership.save()
    assert auth_client.get(reverse('home-visit-reminder'), {'workspace': 'company', 'company_id': first.id}).status_code == 404


def test_non_coordinator_only_sees_assigned_company_appointment(auth_client, user, another_user, appointments):
    value, _ = company(user, coordinator=False)
    appointments(company=value, tenant=another_user, context_kind='company')
    own = appointments(company=value, context_kind='company')
    assert read(auth_client, 'company', company_id=value.id)['visit_id'] == str(own.id)


def test_student_group_requires_current_membership_and_consent(auth_client, user, another_user, appointments):
    visit = appointments(tenant=another_user, context_kind='group')
    group = HousingGroup.objects.create(name='Visit group')
    membership = GroupMembership.objects.create(group=group, user=user, status='active', role='member')
    process = GroupProcess.objects.create(
        group=group, initiated_by=another_user, property=visit.property, visit=visit,
        kind='visit', roster_revision=1, status='submitted',
        participant_ids=[str(user.id)], consented_ids=[],
    )
    assert read(auth_client, 'student') is None
    process.consented_ids = [str(user.id)]
    process.save()
    assert read(auth_client, 'student')['visit_id'] == str(visit.id)
    membership.status = 'left'
    membership.save()
    assert read(auth_client, 'student') is None


def test_empty_and_authentication(auth_client):
    assert read(auth_client) is None
    assert APIClient().get(reverse('home-visit-reminder'), {'workspace': 'individual'}).status_code in (401, 403)
    assert auth_client.get(reverse('home-visit-reminder'), {'workspace': 'company'}).status_code == 400
    assert auth_client.get(reverse('home-visit-reminder'), {'workspace': 'invalid'}).status_code == 400
