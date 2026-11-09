"""A1-02 failing-before case (Sprint 00): inherited Djoser deletion must not bypass closure.

Strict xfail documents the current defect without changing behavior. When Sprint 01 routes
these aliases into the reviewed closure workflow, the test passes, strict xfail turns that
into a failure, and the marker must be removed in the same change.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A1-02: DELETE /auth/users/me/ physically deletes the account (Sprint 01)")
def test_inherited_self_delete_does_not_remove_the_account(auth_client, user):
    response = auth_client.delete(
        "/api/v1/auth/users/me/", {"current_password": "Testpass123!"}, format="json"
    )

    assert User.objects.filter(pk=user.pk).exists(), f"account removed with HTTP {response.status_code}"
    assert response.status_code >= 400
