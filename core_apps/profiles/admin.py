from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "gender", "birth_date"]
    list_display_links = ["id", "user"]
