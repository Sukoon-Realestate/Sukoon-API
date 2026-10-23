import pytest
from django.urls import reverse

from core_apps.features.models import RentalAuditEvent
from core_apps.properties.models import Property


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "action",
        "initial_status",
        "initial_verified",
        "expected_status",
        "expected_verified",
        "audit_action",
        "reason",
    ),
    [
        (
            "approve_selected_properties",
            Property.Status.UNDER_REVIEW,
            False,
            Property.Status.VERIFIED,
            True,
            "approve_admin_property",
            "",
        ),
        (
            "request_property_revisions",
            Property.Status.VERIFIED,
            True,
            Property.Status.NEEDS_REVISION,
            False,
            "request_admin_property_revision",
            "Please update the ownership details.",
        ),
        (
            "reject_selected_properties",
            Property.Status.UNDER_REVIEW,
            False,
            Property.Status.HIDDEN,
            False,
            "reject_admin_property",
            "The listing does not meet the publication requirements.",
        ),
    ],
)
def test_property_admin_moderation_actions_are_audited(
    client,
    superuser,
    user,
    apartment_type,
    cairo_city,
    cairo_governorate,
    action,
    initial_status,
    initial_verified,
    expected_status,
    expected_verified,
    audit_action,
    reason,
):
    property_obj = Property.objects.create(
        owner=user,
        title="Listing awaiting moderation",
        property_type=apartment_type,
        city=cairo_city,
        governorate=cairo_governorate,
        district="Nasr City",
        status=initial_status,
        is_verified=initial_verified,
    )
    client.force_login(superuser)

    response = client.post(
        reverse("admin:properties_property_changelist"),
        {
            "action": action,
            "_selected_action": str(property_obj.pk),
            "index": "0",
            "reason": reason,
        },
    )

    assert response.status_code == 302
    property_obj.refresh_from_db()
    assert property_obj.status == expected_status
    assert property_obj.is_verified is expected_verified
    audit_event = RentalAuditEvent.objects.get(
        subject_kind="property", subject_id=property_obj.id
    )
    assert audit_event.actor == superuser
    assert audit_event.action == audit_action
    assert audit_event.reason == reason


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action", ["request_property_revisions", "reject_selected_properties"]
)
def test_property_admin_requires_reason_for_negative_decisions(
    client,
    superuser,
    user,
    apartment_type,
    cairo_city,
    cairo_governorate,
    action,
):
    property_obj = Property.objects.create(
        owner=user,
        title="Listing awaiting moderation",
        property_type=apartment_type,
        city=cairo_city,
        governorate=cairo_governorate,
        district="Nasr City",
    )
    client.force_login(superuser)

    response = client.post(
        reverse("admin:properties_property_changelist"),
        {
            "action": action,
            "_selected_action": str(property_obj.pk),
            "index": "0",
            "reason": "",
        },
    )

    assert response.status_code == 302
    property_obj.refresh_from_db()
    assert property_obj.status == Property.Status.UNDER_REVIEW
    assert not RentalAuditEvent.objects.filter(
        subject_kind="property", subject_id=property_obj.id
    ).exists()
