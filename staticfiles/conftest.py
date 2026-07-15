import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password="Testpass123!",
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        email="another@example.com",
        first_name="Another",
        last_name="User",
        password="Testpass123!",
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="Adminpass123!",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
