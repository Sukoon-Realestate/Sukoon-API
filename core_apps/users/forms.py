from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

User = get_user_model()


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = ["email", "first_name", "last_name"]


class UserCreationForm(admin_forms.UserCreationForm):
    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ["email", "first_name", "last_name"]

    error_messages = {
        "duplicate_email": "A user with this email already exists.",
    }

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(self.error_messages["duplicate_email"])
        return email
