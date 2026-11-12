"""Set-based independent recovery authority; command authority is still rechecked."""
from django.db.models import BooleanField, Exists, F, Func, OuterRef, Q, Value
from rest_framework.exceptions import PermissionDenied

from ..models import StaffSecurityIdentity, TotpRecoveryDecision, TotpRecoveryRequest
from ..read_pages import prepare_history


class JsonUUIDMember(Func):
    """Parameter-free expression joining a stored UUID to a JSON UUID array."""
    output_field = BooleanField()
    arity = 2

    def as_sqlite(self, compiler, connection, **extra):
        array, array_params = compiler.compile(self.source_expressions[0])
        uuid, uuid_params = compiler.compile(self.source_expressions[1])
        sql = (f"EXISTS (SELECT 1 FROM json_each({array}) AS designated "
               f"WHERE replace(designated.value, '-', '') = {uuid})")
        return sql, array_params + uuid_params

    def as_postgresql(self, compiler, connection, **extra):
        array, array_params = compiler.compile(self.source_expressions[0])
        uuid, uuid_params = compiler.compile(self.source_expressions[1])
        return f"({array} @> jsonb_build_array(({uuid})::text))", array_params + uuid_params


def eligible_identities(*, require_person=True):
    rows = (StaffSecurityIdentity.objects.filter(
        user__is_active=True, user__sensitive_actions_frozen=False,
        user__totpfactor__confirmed_at__isnull=False,
    ).exclude(evidence_reference="").exclude(known_channel_reference="")
        .exclude(user__totpfactor__secret_ciphertext="")
        .filter(Q(user__staff_profile__isnull=True) | Q(user__staff_profile__is_active=True))
        .exclude(user_id__in=TotpRecoveryRequest.objects.filter(active=True).values("user_id")))
    return rows.exclude(person_reference="") if require_person else rows


def owner_identities(*, require_person=True):
    return (eligible_identities(require_person=require_person)
            .exclude(user__staff_profile__role_name="security_recovery_reviewer")
            .filter(Q(user__is_superuser=True) | Q(user__staff_profile__role_name="system_owner")))


def with_availability(rows):
    owners = owner_identities().exclude(user_id=OuterRef("user_id")).exclude(
        person_reference=OuterRef("person_reference")
    )
    designated = (eligible_identities().filter(
        user__staff_profile__role_name="security_recovery_reviewer", designated_owner_reviewer=True,
    ).exclude(user_id=OuterRef("user_id")).exclude(person_reference=OuterRef("person_reference"))
        .filter(JsonUUIDMember(OuterRef("designated_reviewer_ids"), F("id"))))
    return rows.annotate(
        independent_owner=Exists(owners), designated_available=Exists(designated),
    )


def review_available(item):
    if not hasattr(item, "independent_owner"):
        item = with_availability(TotpRecoveryRequest.objects.filter(pk=item.pk)).get()
    return item.independent_owner or (item.owner_request and item.designated_available)


def authorized_rows(user, profile):
    from . import totp, totp_recovery

    rows = TotpRecoveryRequest.objects.filter(active=True)
    try:
        identity = totp_recovery._identity(user)
        totp.require_sensitive_access(user)
        totp.current_factor(user)
    except PermissionDenied:
        return rows.none()
    rows = rows.exclude(user=user).exclude(person_reference=identity.person_reference)
    if not totp_recovery._is_owner(user, profile):
        if not (profile and profile.role_name == "security_recovery_reviewer"
                and identity.designated_owner_reviewer):
            return rows.none()
        owners = owner_identities(require_person=False).exclude(user_id=OuterRef("user_id")).exclude(
            person_reference=OuterRef("person_reference")
        )
        rows = (rows.filter(owner_request=True, created_at__gt=identity.created_at)
                .filter(JsonUUIDMember(F("designated_reviewer_ids"), Value(identity.id)))
                .annotate(owner_available=Exists(owners)).filter(owner_available=False))
    return with_availability(rows.select_related("user", "identity")).order_by("-created_at", "-pk")


def prepare_projections(items, *, page=None):
    return prepare_history(items, TotpRecoveryDecision, "recovery", page=page)
