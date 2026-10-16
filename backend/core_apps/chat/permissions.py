from rest_framework.permissions import BasePermission


class IsParticipant(BasePermission):
    """Object-level permission — only participants of a conversation may access it."""

    def has_object_permission(self, request, view, obj):
        conversation = getattr(obj, "conversation", obj)
        if conversation.kind in {"housing_group", "company_request"}:
            from .services.group_access import authorize

            authorize(conversation, request.user)
            return True
        return conversation.participants.filter(pk=request.user.pk).exists()
