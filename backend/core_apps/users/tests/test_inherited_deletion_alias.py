"""A1-02: inherited Djoser deletion aliases must not bypass reviewed account closure.

Sprint 00 recorded this as a strict xfail (DELETE /auth/users/me/ returned 200 and removed the
account). Sprint 01 routes every alias to the same 409 as the other retired delete routes.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "Testpass123!"


def _self_aliases(user):
    return [
        "/api/v1/auth/users/me/",
        f"/api/v1/auth/users/{user.id}/",
        f"/api/v1/auth/users/{user.id}.json",
    ]


@pytest.mark.django_db
def test_inherited_self_delete_does_not_remove_the_account(auth_client, user):
    for url in _self_aliases(user):
        response = auth_client.delete(url, {"current_password": PASSWORD}, format="json")
        assert User.objects.filter(pk=user.pk).exists(), f"{url} removed the account"
        assert response.status_code == 409, (url, response.status_code)
        assert "account closure review" in response.json()["message"]


@pytest.mark.django_db
def test_wrong_or_missing_password_is_refused_the_same_way(auth_client, user):
    for body in ({}, {"current_password": "wrong"}):
        response = auth_client.delete("/api/v1/auth/users/me/", body, format="json")
        assert response.status_code == 409
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_staff_cannot_delete_another_account_through_the_router(user):
    staff = User.objects.create_user(
        email="staff-delete@example.com", password=PASSWORD, first_name="S", last_name="T",
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(staff)
    response = client.delete(f"/api/v1/auth/users/{user.id}/", {"current_password": PASSWORD}, format="json")
    # Djoser admits staff to any account (CurrentUserOrAdmin); destroy still refuses.
    assert response.status_code == 409
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_non_owner_delete_keeps_the_existing_permission_answer(user, another_user):
    # Unchanged Djoser behavior: CurrentUserOrAdmin answers 403 to a non-owner DELETE
    # (GET answers 404). The object is resolved before the 409, so no new signal is added.
    client = APIClient()
    client.force_authenticate(another_user)
    response = client.delete(f"/api/v1/auth/users/{user.id}/", {"current_password": PASSWORD}, format="json")
    assert response.status_code == 403
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_anonymous_delete_is_unauthenticated(user):
    response = APIClient().delete("/api/v1/auth/users/me/", format="json")
    assert response.status_code == 401
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_self_read_on_the_same_alias_is_unchanged(auth_client, user):
    response = auth_client.get("/api/v1/auth/users/me/")
    assert response.status_code == 200
