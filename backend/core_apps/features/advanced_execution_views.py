from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.http import Http404
from .advanced_execution_models import AdvancedExecution
from .services.planning import planning_api, mutate, page
from .services.advanced_execution.plans import get_plan
from .services.advanced_execution.engine import command
from .services.advanced_execution.projections import payload


@planning_api(["GET"], None)
def inbox(request):
    # Re-evaluate source authority, including revoked corporate membership.
    candidates = AdvancedExecution.objects.filter(actors=request.user)
    authorized = []
    for item in candidates:
        try:
            get_plan(request.user, item.id)
        except (NotFound, PermissionDenied, Http404):
            continue
        authorized.append(item.pk)
    return page(
        request,
        AdvancedExecution.objects.filter(pk__in=authorized).order_by(
            "-updated_at", "pkid"
        ),
        lambda item: payload(item, request.user),
    )


@planning_api(["GET"], None)
def detail(request, execution_id):
    return Response(payload(get_plan(request.user, execution_id), request.user))


@planning_api(["POST"], None)
def action(request, execution_id, action):
    return mutate(
        request,
        f"advanced_execution.{action}.{execution_id}",
        lambda: get_plan(request.user, execution_id, lock=True),
        lambda item, _: command(item, request.user, action, request.data),
        lambda item: payload(item, request.user),
    )
