import pytest
from core_apps.users.forms import UserCreationForm
from core_apps.users.models import User


@pytest.mark.django_db
def test_admin_password_mismatch_is_a_form_error_without_account_creation():
    form = UserCreationForm(
        data={
            "email": "admin-created@example.invalid",
            "first_name": "Synthetic",
            "last_name": "QA",
            "password1": "Synthetic-strong-qa-password-123!",
            "password2": "A-different-qa-password-456!",
        }
    )
    assert not form.is_valid()
    assert "password2" in form.errors
    assert not User.objects.filter(email="admin-created@example.invalid").exists()
