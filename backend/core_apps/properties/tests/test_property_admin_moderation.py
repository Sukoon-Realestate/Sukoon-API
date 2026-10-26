import pytest
from django.urls import reverse

from core_apps.features.models import RentalAuditEvent
from core_apps.properties.models import Property, PropertyImage


@pytest.fixture(autouse=True)
def local_admin_assets(settings):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )


@pytest.mark.django_db
def test_property_requests_admin_lists_filters_and_opens_submissions(
    client, superuser, user, apartment_type, cairo_city, cairo_governorate, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    pending = Property.objects.create(
        owner=user,
        title="Pending submission",
        property_type=apartment_type,
        city=cairo_city,
        governorate=cairo_governorate,
        district="Nasr City",
    )
    verified = Property.objects.create(
        owner=user,
        title="Approved submission",
        property_type=apartment_type,
        city=cairo_city,
        governorate=cairo_governorate,
        district="Nasr City",
        status=Property.Status.VERIFIED,
        is_verified=True,
    )
    client.force_login(superuser)
    url = reverse("admin:properties_propertyrequest_changelist")
    index = client.get(reverse("admin:index"))
    assert url in index.content.decode()

    response = client.get(url)
    assert response.status_code == 200
    assert {obj.pk for obj in response.context["cl"].queryset} == {
        pending.pk,
        verified.pk,
    }
    assert "status" in response.context["cl"].list_display
    assert "is_verified" in response.context["cl"].list_display

    response = client.get(
        url, {"status__exact": "under_review", "is_verified__exact": "0"}
    )
    assert response.status_code == 200
    assert [obj.pk for obj in response.context["cl"].queryset] == [pending.pk]

    response = client.get(
        reverse("admin:properties_propertyrequest_change", args=[pending.pk])
    )
    assert response.status_code == 200
    assert set(response.context["adminform"].form.fields) == {
        "decision",
        "reason",
        "internal_note",
        "expected_version",
        "request_key",
    }


@pytest.mark.django_db
def test_property_request_edit_only_changes_status_and_verification(
    client, superuser, user, apartment_type, cairo_city, cairo_governorate, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    property_obj = Property.objects.create(
        owner=user,
        title="Original title",
        property_type=apartment_type,
        city=cairo_city,
        governorate=cairo_governorate,
        district="Nasr City",
    )
    image = PropertyImage.objects.create(
        property=property_obj, image="properties/original.jpg", name="Original image"
    )
    client.force_login(superuser)
    url = reverse("admin:properties_propertyrequest_change", args=[property_obj.pk])
    response = client.get(url)
    inline = response.context["inline_admin_formsets"][0]
    assert not inline.has_add_permission
    assert not inline.has_change_permission
    assert not inline.has_delete_permission
    payload = {
        "decision": "approve",
        "expected_version": response.context["adminform"].form.initial[
            "expected_version"
        ],
        "request_key": str(response.context["adminform"].form.initial["request_key"]),
        "status": Property.Status.VERIFIED,
        "is_verified": "on",
        "title": "Tampered title",
        "price": "999999",
        "_save": "Save",
    }
    for field in inline.formset.management_form:
        payload[field.html_name] = field.value()
    for form in inline.formset.forms:
        for field in form.hidden_fields():
            payload[field.html_name] = field.value()
        payload[f"{form.prefix}-name"] = "Tampered image"
        payload[f"{form.prefix}-DELETE"] = "on"

    response = client.post(url, payload)
    assert response.status_code == 302
    property_obj.refresh_from_db()
    image.refresh_from_db()
    assert property_obj.status == Property.Status.VERIFIED
    assert property_obj.is_verified
    assert property_obj.title == "Original title"
    assert property_obj.price == 0
    assert image.name == "Original image"


@pytest.mark.django_db
def test_property_requests_admin_reuses_property_permissions(client, user, settings):
    from django.contrib.auth.models import Permission

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    client.force_login(user)
    url = reverse("admin:properties_propertyrequest_changelist")
    assert client.get(url).status_code == 403

    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="properties", codename="view_property"
        )
    )
    response = client.get(url)
    assert response.status_code == 200
    assert not response.context["has_add_permission"]
    assert "delete_selected" not in response.context["cl"].model_admin.get_actions(
        response.wsgi_request
    )


@pytest.mark.django_db
@pytest.mark.parametrize("admin_model", ["property", "propertyrequest"])
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
            "approve",
            Property.Status.UNDER_REVIEW,
            False,
            Property.Status.VERIFIED,
            True,
            "property.moderation.approve",
            "",
        ),
        (
            "request_revision",
            Property.Status.VERIFIED,
            True,
            Property.Status.NEEDS_REVISION,
            False,
            "property.moderation.request_revision",
            "Please update the ownership details.",
        ),
        (
            "reject",
            Property.Status.UNDER_REVIEW,
            False,
            Property.Status.NEEDS_REVISION,
            False,
            "property.moderation.reject",
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
    admin_model,
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

    url = reverse(f"admin:properties_{admin_model}_change", args=[property_obj.pk])
    response = client.get(url)
    form = response.context["adminform"].form
    payload = {
        "decision": action,
        "reason": reason,
        "expected_version": form.initial["expected_version"],
        "request_key": str(form.initial["request_key"]),
        "_save": "Save",
    }
    for inline in response.context["inline_admin_formsets"]:
        for field in inline.formset.management_form:
            payload[field.html_name] = field.value()
    response = client.post(url, payload)

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
@pytest.mark.parametrize("action", ["request_revision", "reject"])
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

    url = reverse("admin:properties_property_change", args=[property_obj.pk])
    response = client.get(url)
    form = response.context["adminform"].form
    payload = {
        "decision": action,
        "reason": "",
        "expected_version": form.initial["expected_version"],
        "request_key": str(form.initial["request_key"]),
        "_save": "Save",
    }
    for inline in response.context["inline_admin_formsets"]:
        for field in inline.formset.management_form:
            payload[field.html_name] = field.value()
    response = client.post(url, payload)
    assert response.status_code == 200
    assert "reason" in response.context["adminform"].form.errors
    property_obj.refresh_from_db()
    assert property_obj.status == Property.Status.UNDER_REVIEW
    assert not RentalAuditEvent.objects.filter(
        subject_kind="property", subject_id=property_obj.id
    ).exists()
