from rest_framework.permissions import BasePermission


class IsParticipant(BasePermission):
    """Object-level permission — only participants of a conversation may access it."""

    def has_object_permission(self, request, view, obj):
        conversation = getattr(obj, "conversation", obj)
        return conversation.participants.filter(pk=request.user.pk).exists()
