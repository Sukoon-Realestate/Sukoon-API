from django.contrib import admin

from core_apps.chat.models import Conversation, ConversationParticipant, Message


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "last_message_preview", "last_message_at", "created_at")
    search_fields = ("id", "last_message_preview")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ConversationParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    search_fields = ("id", "content", "sender__email")
    readonly_fields = ("id", "created_at", "updated_at")
    list_filter = ("created_at",)
