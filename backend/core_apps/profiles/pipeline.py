from .models import Profile


def save_profile(backend, user, response, *args, **kwargs):
    Profile.objects.get_or_create(user=user)
    if getattr(backend, "name", None) == "google-oauth2":
        from core_apps.users.services.google_avatar import sync_google_avatar

        sync_google_avatar(user, response.get("picture"))
