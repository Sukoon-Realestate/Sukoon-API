from django.contrib import admin
from .models import Profile, UserSettings


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "gender", "birth_date", "phone_number", "national_id"]
    list_display_links = ["id", "user"]


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "visit_notifications",
        "new_properties_in_area",
        "owner_messages",
        "promotions_and_updates",
        "always_hide_mobile_number",
        "share_location_for_search",
        "show_profile_in_search",
    ]
    list_display_links = ["id", "user"]

