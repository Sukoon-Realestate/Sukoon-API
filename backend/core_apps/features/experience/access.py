from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

FEATURES = ('action_center', 'costs', 'discovery', 'suggestions', 'preparation', 'quality', 'sync', 'media')


def enabled(feature):
    from core_apps.common.mvp_scope import enabled as mvp_enabled
    if mvp_enabled() and feature == 'preparation':
        return False
    return feature in getattr(settings, 'SOKOUN_EXPERIENCE_FEATURES', ())


def require(feature):
    if not enabled(feature):
        raise NotFound('This experience feature is not available.')


def scope_for(request):
    user = request.user
    if not user.is_active or getattr(user, 'closed_at', None):
        raise PermissionDenied('An active account is required.')
    workspace = request.query_params.get('workspace', 'individual')
    if workspace not in {'individual', 'student', 'owner', 'company'}:
        raise ValidationError({'workspace': 'Unknown workspace.'})
    company = request.headers.get('X-Sukoon-Company-Id', '')
    role = request.headers.get('X-Sukoon-Company-Role', '')
    if workspace == 'company':
        from ..services.company.access import company_for
        from ..services.company.role_context import selected
        if not company or not role:
            raise PermissionDenied('Choose a current company role first.')
        current = company_for(user, company)
        selected(user, current)
        return f'company/{current.id}/{role}'
    if company or role:
        raise PermissionDenied('Leave the company context before using personal tools.')
    return workspace


def preferences(user, scope, *, lock=False):
    from core_apps.users.models import User
    from .models import ExperiencePreferences
    if lock:
        User.objects.select_for_update().get(pk=user.pk)
    item, _ = ExperiencePreferences.objects.get_or_create(user=user, scope=scope)
    return ExperiencePreferences.objects.select_for_update().get(pk=item.pk) if lock else item
