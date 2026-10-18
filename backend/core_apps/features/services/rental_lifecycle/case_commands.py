"""One authorization/locking/receipt boundary for API and operations console."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.properties.models import Property
from core_apps.users.models import User
from ...models import Lease
from .cases import case_queryset, case_payload, case_action
from .common import command, audit


def act_on_case(user, case_id, data, *, command_data=None):
    def authorize():
        current = User.objects.get(pk=user.pk)
        from core_apps.admin_api.models import StaffProfile

        StaffProfile.objects.select_for_update().filter(user=current).first()
        item = get_object_or_404(case_queryset(current), id=case_id)
        if item.property_id:
            Property.objects.select_for_update().get(pk=item.property_id)
        if item.lease_id:
            Lease.objects.select_for_update().get(pk=item.lease_id)
        return get_object_or_404(
            case_queryset(current).select_for_update(of=("self",)), id=case_id
        )

    def execute(item):
        current = User.objects.get(pk=user.pk)
        item = case_action(item, current, data)
        return item, case_payload(item, current), 200

    try:
        return command(
            user=user,
            operation=f"rental_case.action.{case_id}",
            data=command_data if command_data is not None else data,
            authorize=authorize,
            execute=execute,
        )
    except PermissionDenied:
        item = case_queryset(user).filter(id=case_id).first()
        if item is not None:
            audit(
                item,
                user,
                "case.command_denied",
                "Current independent authority was not sufficient.",
                {"action": str(data.get("action", ""))[:60]},
            )
        raise
