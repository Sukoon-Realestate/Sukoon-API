"""Existing editor scope for account, discovery, property and help content."""
from rest_framework.exceptions import PermissionDenied
from core_apps.common.mvp_scope import enabled

KINDS = frozenset({'pages', 'contacts', 'articles', 'releases', 'governorates',
                   'cities', 'districts', 'property_types'})
WORKSPACES = frozenset({'tenant', 'individual', 'owner', 'both', 'all', 'account'})


def kinds(registry):
    return [kind for kind in registry if not enabled() or kind in KINDS]


def require_kind(kind):
    if enabled() and kind not in KINDS:
        raise PermissionDenied('This catalog is deferred for the MVP release.', code='mvp_feature_deferred')


def require_workspace(values):
    if not isinstance(values, dict) or 'workspace' not in values:
        return
    workspace = values['workspace']
    if enabled() and (not isinstance(workspace, str) or workspace not in WORKSPACES):
        raise PermissionDenied('This content audience is deferred for the MVP release.', code='mvp_feature_deferred')


def allows_choice(field, value):
    return field != 'workspace' or not enabled() or value in WORKSPACES


def query(queryset):
    if enabled() and any(field.name == 'workspace' for field in queryset.model._meta.fields):
        return queryset.filter(workspace__in=WORKSPACES)
    return queryset
