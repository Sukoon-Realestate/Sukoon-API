"""Project the existing D26 assurance contract onto active account consumers."""
from copy import deepcopy
from rest_framework.exceptions import PermissionDenied
from core_apps.common.mvp_scope import enabled

ACCOUNT_ACTIONS = (
    'account.closure.request', 'account.closure.review', 'account.contact.change',
    'account.mfa.manage', 'account.totp.recovery.review',
)


def codes(catalog):
    return ('D26',) if enabled() else tuple(catalog)


def project(code, definition):
    spec = deepcopy(definition)
    if not enabled():
        return spec
    if code != 'D26':
        raise PermissionDenied('This policy family is deferred for the MVP release.', code='mvp_feature_deferred')
    # These actions already consume approved D26 proofs. The projection neither
    # adds a consumer nor changes a previous publication or accepted snapshot.
    spec['scope'] = list(ACCOUNT_ACTIONS)
    spec['title'] = ['Account security verification', 'التحقق من أمان الحساب']
    spec['description'] = [
        'Fresh verification is bound to the account, session, action and reviewed details. Current staff authority remains independently required for staff actions.',
        'يرتبط التحقق الحديث بالحساب والجلسة والإجراء والتفاصيل المراجعة. تظل صلاحية الموظف الحالية مطلوبة بصورة مستقلة لإجراءات الإدارة.',
    ]
    spec['consumer'] = 'users.services.sensitive_actions.begin/verify/consume; existing contact, MFA, recovery-review and account-closure consumers'
    return spec
