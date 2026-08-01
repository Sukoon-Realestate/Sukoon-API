from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a property to edit/delete it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsTenantOrPropertyOwner(permissions.BasePermission):
    """
    Custom permission to only allow tenants of a visit request or owners of the property to view/edit it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.tenant == request.user or obj.property.owner == request.user
