"""Shared transport-only validation for identity command bodies."""
from collections.abc import Mapping
from rest_framework import serializers
from rest_framework.views import APIView


class ObjectBodyMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not isinstance(request.data, Mapping):
            raise serializers.ValidationError({"non_field_errors": ["Expected an object or form body."]})


class IdentityAPIView(ObjectBodyMixin, APIView):
    pass
