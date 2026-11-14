"""Request-local campaign preview facts, prepared in bounded account batches.

These facts describe a preview only. Dispatch continues to recheck consent,
workspace authority and device/session validity immediately before delivery.
"""

from itertools import islice

from django.db.models import Exists, F, OuterRef, Q
from django.utils import timezone

from core_apps.common.mvp_scope import enabled
from core_apps.features.company_models import CompanyMembership
from core_apps.features.models import Lease, RentalInterest
from core_apps.features.planning_models import HousingRequest
from core_apps.features.student_models import StudentProfile
from core_apps.notifications.models import DeviceToken, NotificationScopePreference
from core_apps.notifications.services.preferences import CATEGORY_FIELDS
from core_apps.properties.models import Property, PropertyVisit


def candidates(query, audience):
    """Prepare membership predicates in SQL instead of querying each account."""
    facts = {
        "campaign_owner": Exists(Property.objects.filter(owner_id=OuterRef("pk"))),
    }
    visits = PropertyVisit.objects.filter(tenant_id=OuterRef("pk"))
    if enabled():
        facts["campaign_renter"] = Exists(
            visits.filter(
                company__isnull=True,
                academic_plan__isnull=True,
                groupprocess__isnull=True,
            )
        )
    else:
        facts.update(
            campaign_student=Exists(
                StudentProfile.objects.filter(user_id=OuterRef("pk"))
            ),
            campaign_company=Exists(
                CompanyMembership.objects.filter(
                    user_id=OuterRef("pk"),
                    is_active=True,
                    company__review_status="verified",
                )
            ),
            campaign_renter=(
                Exists(Lease.objects.filter(tenant_id=OuterRef("pk")))
                | Exists(RentalInterest.objects.filter(tenant_id=OuterRef("pk")))
                | Exists(HousingRequest.objects.filter(user_id=OuterRef("pk")))
                | Exists(visits)
            ),
        )
    query = query.select_related("settings").annotate(**facts)
    predicate = {
        "landlords": {"campaign_owner": True},
        "tenants": {"campaign_renter": True},
        "verified": {"is_verified": True},
    }
    if not enabled():
        predicate.update(
            students={"campaign_student": True}, companies={"campaign_company": True}
        )
    return query.filter(**predicate.get(audience, {}))


def spaces(user, audience):
    if (
        not user.is_active
        or user.closed_at
        or (audience == "verified" and not user.is_verified)
    ):
        return set()
    result = {"individual"}
    if user.campaign_owner:
        result.add("owner")
    if enabled():
        if audience in {"students", "companies"}:
            return set()
    else:
        if user.campaign_student:
            result.add("student")
        if user.campaign_company:
            result.add("company")
    for target, scope in [
        ("landlords", "owner"),
        ("students", "student"),
        ("companies", "company"),
    ]:
        if audience == target:
            return result & {scope}
    if audience == "tenants":
        return result & {"individual", "student"} if user.campaign_renter else set()
    return result


def batches(query, audience, size=500):
    rows = candidates(query, audience).iterator(chunk_size=size)
    while batch := list(islice(rows, size)):
        ids = [user.pk for user in batch]
        preferences = {
            (row.user_id, row.scope): row
            for row in NotificationScopePreference.objects.filter(user_id__in=ids)
        }
        missing = []
        for user in batch:
            user.campaign_spaces = spaces(user, audience)
            original = getattr(user, "settings", None)
            defaults = (
                {key: getattr(original, key) for key in CATEGORY_FIELDS}
                if original
                else {}
            )
            for scope in user.campaign_spaces:
                if (user.pk, scope) not in preferences:
                    missing.append(
                        NotificationScopePreference(user=user, scope=scope, **defaults)
                    )
        if missing:
            # Preserve lazy preference initialization without N get-or-create calls.
            # A simultaneous preference change wins the unique constraint.
            NotificationScopePreference.objects.bulk_create(
                missing, ignore_conflicts=True, batch_size=500
            )
            preferences = {
                (row.user_id, row.scope): row
                for row in NotificationScopePreference.objects.filter(user_id__in=ids)
            }
        devices = (
            DeviceToken.objects.filter(user_id__in=ids, is_active=True)
            .filter(
                Q(
                    auth_session__isnull=True,
                    user__security_epoch=0,
                    user__requires_bound_session=False,
                )
                | Q(
                    auth_session__isnull=False,
                    auth_session__revoked_at__isnull=True,
                    auth_session__expires_at__gt=timezone.now(),
                    auth_session__security_epoch=F("user__security_epoch"),
                    auth_session__user_id=F("user_id"),
                )
            )
            .order_by("user_id", "-updated_at", "-pk")
        )
        # DISTINCT ON is PostgreSQL-only. The same order supports both engines.
        latest = {}
        for device in devices.iterator(chunk_size=size):
            latest.setdefault(device.user_id, device)
        for user in batch:
            user.campaign_preferences = {
                scope: preferences[user.pk, scope] for scope in user.campaign_spaces
            }
            user.campaign_device = latest.get(user.pk)
        yield from batch
