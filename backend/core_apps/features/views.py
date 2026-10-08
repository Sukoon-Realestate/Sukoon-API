import copy
import hashlib
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.common.models import ContentView
from core_apps.properties.models import Property, PropertyVisit, SavedProperty

from .models import (
    BoostCampaign,
    CheckoutSession,
    IdempotencyRecord,
    Lease,
    ListingSuggestion,
    RentInvoice,
    SearchAlert,
    SigningSession,
    TenancyInvitation,
)
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .serializers import (
    AlertCreateSerializer,
    BoostCampaignSerializer,
    LeaseCreateSerializer,
    LeaseSerializer,
    RentInvoiceSerializer,
    RevisionRequestSerializer,
    SearchAlertSerializer,
    TenancyInvitationCreateSerializer,
    TenancyInvitationResponseSerializer,
    TenancyInvitationSerializer,
)
from .services.tenancy_invitations import (
    InvitationConflict,
    LIVE_LEASE_STATUSES,
    create_notification_for_invitation,
    create_notification_for_response,
    invitation_is_eligible,
    localized,
    refresh_effective_status,
    resolve_offer_snapshot,
    validate_accounts,
    validate_source_relationship,
)

User = get_user_model()
FEATURE_DECORATORS = [api_view]
BOOST_OPTIONS = {
    "week": {
        "duration_days": 7,
        "title_en": "Free promotion for 7 days",
        "title_ar": "ترويج مجاني لمدة 7 أيام",
    },
    "month": {
        "duration_days": 30,
        "title_en": "Free promotion for 30 days",
        "title_ar": "ترويج مجاني لمدة 30 يومًا",
    },
}
LEASE_TEMPLATES = [
    {
        "id": "eg-residential-v1",
        "title": "Residential lease",
        "jurisdiction": "EG",
        "language": "ar",
        "version": "1",
    }
]


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with current server state."


def _fingerprint(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def _replay(user, operation, request_key, payload):
    record = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=request_key
    ).first()
    if not record:
        return None
    if record.fingerprint != _fingerprint(payload):
        raise Conflict(
            "This request_key was already used with a different payload.",
            code="request_key_conflict",
        )
    return Response(record.response_data, status=record.response_status)


def _remember(user, operation, request_key, payload, data, response_status):
    IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=request_key,
        fingerprint=_fingerprint(payload),
        response_data=data,
        response_status=response_status,
    )


def _paginate(request, queryset, serializer_class):
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def configuration(request):
    workspace = request.query_params.get("workspace")
    lang = request.query_params.get("lang", "en")
    if workspace not in {"owner", "tenant"}:
        raise ValidationError({"workspace": "Must be owner or tenant."})
    options = []
    if workspace == "owner":
        options = [
            {
                "id": key,
                "title": value["title_ar" if lang == "ar" else "title_en"],
                "duration_days": value["duration_days"],
            }
            for key, value in BOOST_OPTIONS.items()
        ]
    return Response(
        {
            "workspace": workspace,
            "boost_options": options,
            "alert_cadences": ["instant", "daily"] if workspace == "tenant" else [],
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def boost_campaigns(request):
    if request.method == "GET":
        return _paginate(
            request,
            BoostCampaign.objects.filter(owner=request.user).select_related("property"),
            BoostCampaignSerializer,
        )
    required = {"property_id", "option_id", "request_key"}
    if not required.issubset(request.data):
        raise ValidationError(
            {key: "This field is required." for key in required - set(request.data)}
        )
    replay = _replay(
        request.user, "boost.create", request.data["request_key"], request.data
    )
    if replay:
        return replay
    option = BOOST_OPTIONS.get(request.data["option_id"])
    if not option:
        raise ValidationError({"option_id": "Unsupported promotion option."})
    property_obj = get_object_or_404(
        Property, id=request.data["property_id"], owner=request.user
    )
    if property_obj.status != Property.Status.VERIFIED or not property_obj.is_verified:
        raise ValidationError("Only published, verified properties can be promoted.")
    now = timezone.now()
    if BoostCampaign.objects.filter(
        property=property_obj, status__in=["pending", "active"], ends_at__gt=now
    ).exists():
        raise ValidationError("This property already has an active campaign.")
    with transaction.atomic():
        campaign = BoostCampaign.objects.create(
            owner=request.user,
            property=property_obj,
            option_id=request.data["option_id"],
            duration_days=option["duration_days"],
            starts_at=now,
            ends_at=now + timedelta(days=option["duration_days"]),
            status=BoostCampaign.Status.ACTIVE,
        )
        data = {
            "id": str(campaign.id),
            "subject_id": str(property_obj.id),
            "status": campaign.status,
            "message": "Promotion activated.",
        }
        _remember(
            request.user,
            "boost.create",
            request.data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def search_alerts(request):
    if request.method == "GET":
        return _paginate(
            request,
            SearchAlert.objects.filter(user=request.user, deleted_at__isnull=True),
            SearchAlertSerializer,
        )
    serializer = AlertCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    replay = _replay(request.user, "alert.create", payload["request_key"], request.data)
    if replay:
        return replay
    with transaction.atomic():
        alert = SearchAlert.objects.create(
            user=request.user,
            name=payload["name"],
            cadence=payload["cadence"],
            filters=payload["filters"],
        )
        data = {"id": str(alert.id), "subject_id": str(alert.id), "status": "active"}
        _remember(
            request.user,
            "alert.create",
            payload["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def search_alert_detail(request, alert_id):
    alert = get_object_or_404(
        SearchAlert, id=alert_id, user=request.user, deleted_at__isnull=True
    )
    if request.method == "GET":
        return Response(SearchAlertSerializer(alert, context={"request": request}).data)
    serializer = RevisionRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data["revision"] != alert.revision:
        return Response(
            {"message": "Alert revision conflict."}, status=status.HTTP_409_CONFLICT
        )
    operation = "alert.delete" if request.method == "DELETE" else "alert.update"
    replay = _replay(
        request.user, operation, serializer.validated_data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        alert = SearchAlert.objects.select_for_update().get(pk=alert.pk)
        if request.method == "DELETE":
            alert.enabled = False
            alert.deleted_at = timezone.now()
            action_status = "cancelled"
        else:
            if "enabled" not in request.data or not isinstance(
                request.data["enabled"], bool
            ):
                raise ValidationError({"enabled": "A boolean is required."})
            alert.enabled = request.data["enabled"]
            action_status = "active" if alert.enabled else "paused"
        alert.revision += 1
        alert.save(update_fields=["enabled", "deleted_at", "revision", "updated_at"])
        data = {
            "id": str(alert.id),
            "subject_id": str(alert.id),
            "status": action_status,
            "revision": alert.revision,
        }
        _remember(
            request.user,
            operation,
            serializer.validated_data["request_key"],
            request.data,
            data,
            200,
        )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_analytics(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    try:
        period_days = int(request.query_params.get("period_days", 30))
    except ValueError:
        raise ValidationError({"period_days": "Must be 7, 30, or 90."})
    if period_days not in {7, 30, 90}:
        raise ValidationError({"period_days": "Must be 7, 30, or 90."})
    since = timezone.now() - timedelta(days=period_days)
    ct = ContentType.objects.get_for_model(Property)
    views = ContentView.objects.filter(
        content_type=ct, object_id=property_obj.pkid, last_viewed__gte=since
    ).count()
    visits = PropertyVisit.objects.filter(
        property=property_obj, created_at__gte=since
    ).count()
    conversion = round((visits / views) * 100, 2) if views else None
    saved = SavedProperty.objects.filter(
        property=property_obj, created_at__gte=since
    ).count()
    return Response(
        {
            "property_id": str(property_obj.id),
            "period_days": period_days,
            "measured_at": timezone.now().isoformat(),
            "methodology": (
                "Unique stored property views and created visit requests in the "
                "selected Africa/Cairo reporting window."
            ),
            "metrics": [
                {
                    "key": "unique_views",
                    "label": "Unique visitors",
                    "value": views,
                    "unit": "count",
                    "definition": "Stored distinct property view records in the period.",
                },
                {
                    "key": "viewing_conversion",
                    "label": "Viewing request rate",
                    "value": conversion,
                    "unit": "percent",
                    "definition": "Visit requests created in the period divided by unique stored views.",
                },
                {
                    "key": "saved_count",
                    "label": "Saves",
                    "value": saved,
                    "unit": "count",
                    "definition": "New saves in the period.",
                },
            ],
            "export_url": "",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def listing_suggestions(request):
    required = {"facts", "language", "request_key"}
    if not required.issubset(request.data):
        raise ValidationError(
            {key: "This field is required." for key in required - set(request.data)}
        )
    if request.data["language"] not in {"ar", "en"} or not isinstance(
        request.data["facts"], dict
    ):
        raise ValidationError("language must be ar/en and facts must be an object.")
    replay = _replay(
        request.user, "suggestion.create", request.data["request_key"], request.data
    )
    if replay:
        return replay
    property_obj = None
    if request.data.get("property_id"):
        property_obj = get_object_or_404(
            Property, id=request.data["property_id"], owner=request.user
        )
    facts = request.data["facts"]
    title = str(
        facts.get("title")
        or ("مسكن مميز" if request.data["language"] == "ar" else "A distinctive home")
    )[:150]
    description = str(facts.get("description") or "").strip()
    if not description:
        place = facts.get("district") or facts.get("governorate") or ""
        description = (
            f"مسكن متاح في {place}"
            if request.data["language"] == "ar"
            else f"A home available in {place}"
        ).strip()
    warnings = (
        []
        if facts.get("description")
        else ["Description was generated only from the supplied public facts."]
    )
    with transaction.atomic():
        suggestion = ListingSuggestion.objects.create(
            owner=request.user,
            property=property_obj,
            language=request.data["language"],
            facts=facts,
            suggested_title=title,
            suggested_description=description[:5000],
            warnings=warnings,
        )
        data = {
            "id": str(suggestion.id),
            "property_id": str(property_obj.id) if property_obj else "",
            "suggested_title": suggestion.suggested_title,
            "suggested_description": suggestion.suggested_description,
            "warnings": warnings,
        }
        _remember(
            request.user,
            "suggestion.create",
            request.data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_configuration(request):
    return Response({"can_create": True, "templates": LEASE_TEMPLATES})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_tenants(request):
    property_id = request.query_params.get("property_id")
    if not property_id:
        raise ValidationError({"property_id": "This query parameter is required."})
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active owner account is required.")
    queryset = TenancyInvitation.objects.filter(
        property=property_obj,
        owner=request.user,
        status=TenancyInvitation.Status.ACCEPTED,
        lease__isnull=True,
    ).select_related("property", "property__owner", "owner", "tenant", "lease")
    offer_id = request.query_params.get("offer_id")
    if offer_id:
        queryset = queryset.filter(offer_id=offer_id)
    eligible = []
    seen = set()
    for invitation in queryset.order_by("-created_at", "-id"):
        refresh_effective_status(invitation)
        if invitation_is_eligible(invitation) and invitation.tenant_id not in seen:
            seen.add(invitation.tenant_id)
            eligible.append(invitation)
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(eligible, request)
    return paginator.get_paginated_response(
        [
            {
                "id": str(invitation.tenant.id),
                "display_name": invitation.tenant.get_full_name,
            }
            for invitation in page
        ]
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitations(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        if workspace == "owner":
            queryset = TenancyInvitation.objects.filter(owner=request.user)
        elif workspace == "tenant":
            queryset = TenancyInvitation.objects.filter(tenant=request.user)
        else:
            raise ValidationError({"workspace": "Must be owner or tenant."})
        property_id = request.query_params.get("property_id")
        if property_id:
            if workspace == "owner":
                get_object_or_404(Property, id=property_id, owner=request.user)
            queryset = queryset.filter(property__id=property_id)
        queryset = queryset.select_related(
            "property", "property__owner", "owner", "tenant", "lease"
        ).order_by("-created_at", "-id")
        for invitation in list(queryset):
            refresh_effective_status(invitation)
        return _paginate(request, queryset.all(), TenancyInvitationSerializer)

    serializer = TenancyInvitationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"),
        id=data_in["property_id"],
        owner=request.user,
    )
    tenant = get_object_or_404(User, id=data_in["tenant_id"])
    validate_accounts(request.user, tenant, request)
    validate_source_relationship(property_obj, tenant, request)
    replay = _replay(
        request.user,
        "tenancy_invitation.create",
        data_in["request_key"],
        request.data,
    )
    if replay:
        return replay
    if property_obj.status != Property.Status.VERIFIED or not property_obj.is_verified:
        raise InvitationConflict(
            localized(
                request,
                "The property is not currently available for leasing.",
                "العقار غير متاح حاليًا للإيجار.",
            )
        )
    try:
        with transaction.atomic():
            property_obj = get_object_or_404(
                Property.objects.select_for_update().select_related("owner"),
                pk=property_obj.pk,
                owner=request.user,
            )
            tenant = get_object_or_404(User.objects.select_for_update(), pk=tenant.pk)
            validate_accounts(request.user, tenant, request)
            validate_source_relationship(property_obj, tenant, request)
            replay = _replay(
                request.user,
                "tenancy_invitation.create",
                data_in["request_key"],
                request.data,
            )
            if replay:
                return replay
            if (
                property_obj.status != Property.Status.VERIFIED
                or not property_obj.is_verified
            ):
                raise InvitationConflict(
                    localized(
                        request,
                        "The property is not currently available for leasing.",
                        "العقار غير متاح حاليًا للإيجار.",
                    )
                )
            offer_id, snapshot = resolve_offer_snapshot(
                property_obj,
                data_in.get("offer_id", ""),
                data_in.get("expected_offer_revision"),
                request,
            )
            if Lease.objects.filter(
                property=property_obj,
                offer_id=offer_id,
                status__in=LIVE_LEASE_STATUSES,
            ).exists():
                raise InvitationConflict(
                    localized(
                        request,
                        "The accommodation already has a conflicting lease.",
                        "يوجد عقد متعارض لمكان الإقامة.",
                    )
                )
            live = list(
                TenancyInvitation.objects.select_for_update()
                .filter(
                    owner=request.user,
                    property=property_obj,
                    tenant=tenant,
                    offer_id=offer_id,
                    status__in=[
                        TenancyInvitation.Status.PENDING,
                        TenancyInvitation.Status.ACCEPTED,
                    ],
                    lease__isnull=True,
                )
                .select_related(
                    "property", "property__owner", "owner", "tenant", "lease"
                )
            )
            for existing in live:
                refresh_effective_status(existing)
            if any(
                item.status
                in [
                    TenancyInvitation.Status.PENDING,
                    TenancyInvitation.Status.ACCEPTED,
                ]
                for item in live
            ):
                raise InvitationConflict(
                    localized(
                        request,
                        "A live invitation already exists for this accommodation.",
                        "توجد دعوة سارية بالفعل لمكان الإقامة هذا.",
                    )
                )
            invitation = TenancyInvitation.objects.create(
                property=property_obj,
                owner=request.user,
                tenant=tenant,
                offer_id=offer_id,
                offer_snapshot=snapshot,
                expires_at=timezone.now() + timedelta(days=7),
                initiated_by=request.user,
            )
            output = TenancyInvitationSerializer(
                invitation, context={"request": request}
            ).data
            _remember(
                request.user,
                "tenancy_invitation.create",
                data_in["request_key"],
                request.data,
                output,
                201,
            )
            create_notification_for_invitation(request, invitation)
    except IntegrityError:
        replay = _replay(
            request.user,
            "tenancy_invitation.create",
            data_in["request_key"],
            request.data,
        )
        if replay:
            return replay
        raise InvitationConflict(
            localized(
                request,
                "A live invitation already exists for this accommodation.",
                "توجد دعوة سارية بالفعل لمكان الإقامة هذا.",
            )
        )
    return Response(output, status=status.HTTP_201_CREATED)


def _participant_invitation(request, invitation_id):
    invitation = get_object_or_404(
        TenancyInvitation.objects.select_related(
            "property", "property__owner", "owner", "tenant", "lease"
        ),
        id=invitation_id,
    )
    if request.user not in (invitation.owner, invitation.tenant):
        raise NotFound()
    return invitation


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_detail(request, invitation_id):
    invitation = _participant_invitation(request, invitation_id)
    refresh_effective_status(invitation)
    return Response(
        TenancyInvitationSerializer(invitation, context={"request": request}).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_respond(request, invitation_id):
    visible = _participant_invitation(request, invitation_id)
    if request.user != visible.tenant:
        raise PermissionDenied("Only the addressed tenant can respond.")
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active tenant account is required.")
    serializer = TenancyInvitationResponseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    operation = f"tenancy_invitation.respond.{invitation_id}"
    replay = _replay(request.user, operation, data_in["request_key"], request.data)
    if replay:
        return replay
    with transaction.atomic():
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update().select_related(
                "property", "property__owner", "owner", "tenant", "lease"
            ),
            id=invitation_id,
            tenant=request.user,
        )
        replay = _replay(
            request.user, operation, data_in["request_key"], request.data
        )
        if replay:
            return replay
        refresh_effective_status(invitation)
        if invitation.status != TenancyInvitation.Status.PENDING:
            return Response(
                {"message": "This invitation can no longer be answered."},
                status=status.HTTP_409_CONFLICT,
            )
        if data_in["revision"] != invitation.revision:
            raise InvitationConflict("Invitation revision conflict.")
        now = timezone.now()
        invitation.status = data_in["decision"]
        invitation.revision += 1
        invitation.responded_by = request.user
        fields = ["status", "revision", "responded_by", "updated_at"]
        if invitation.status == TenancyInvitation.Status.ACCEPTED:
            invitation.accepted_at = now
            fields.append("accepted_at")
        else:
            invitation.rejected_at = now
            fields.append("rejected_at")
        invitation.save(update_fields=fields)
        output = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        _remember(
            request.user,
            operation,
            data_in["request_key"],
            request.data,
            output,
            200,
        )
        create_notification_for_response(request, invitation)
    return Response(output)


def _lease_queryset(user, workspace):
    if workspace == "owner":
        return Lease.objects.filter(owner=user)
    if workspace == "tenant":
        return Lease.objects.filter(tenant=user)
    raise ValidationError({"workspace": "Must be owner or tenant."})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def leases(request):
    if request.method == "GET":
        queryset = _lease_queryset(
            request.user, request.query_params.get("workspace")
        ).select_related("property", "owner", "tenant")
        if request.query_params.get("property_id"):
            queryset = queryset.filter(property__id=request.query_params["property_id"])
        return _paginate(request, queryset, LeaseSerializer)
    serializer = LeaseCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"),
        id=data_in["property_id"],
        owner=request.user,
    )
    tenant = get_object_or_404(User, id=data_in["tenant_id"])
    validate_accounts(request.user, tenant, request)
    replay = _replay(request.user, "lease.create", data_in["request_key"], request.data)
    if replay:
        return replay
    template = next(
        (
            item
            for item in LEASE_TEMPLATES
            if item["id"] == data_in["template_id"]
            and item["version"] == data_in["template_version"]
        ),
        None,
    )
    if not template:
        raise ValidationError({"template_id": "Unsupported template or version."})
    try:
        with transaction.atomic():
            property_obj = get_object_or_404(
                Property.objects.select_for_update().select_related("owner"),
                pk=property_obj.pk,
                owner=request.user,
            )
            tenant = get_object_or_404(User.objects.select_for_update(), pk=tenant.pk)
            validate_accounts(request.user, tenant, request)
            replay = _replay(
                request.user, "lease.create", data_in["request_key"], request.data
            )
            if replay:
                return replay
            offer_id = str(data_in.get("offer_id") or "")
            invitations = list(
                TenancyInvitation.objects.select_for_update()
                .filter(
                    property=property_obj,
                    owner=request.user,
                    tenant=tenant,
                    offer_id=offer_id,
                    status=TenancyInvitation.Status.ACCEPTED,
                    lease__isnull=True,
                )
                .select_related(
                    "property", "property__owner", "owner", "tenant", "lease"
                )
                .order_by("-created_at", "-id")
            )
            for item in invitations:
                refresh_effective_status(item)
            invitation = next(
                (item for item in invitations if invitation_is_eligible(item)), None
            )
            if not invitation:
                raise InvitationConflict(
                    localized(
                        request,
                        "The selected tenant is no longer eligible for this accommodation.",
                        "لم يعد المستأجر المحدد مؤهلاً لمكان الإقامة هذا.",
                    )
                )
            lease = Lease.objects.create(
                property=property_obj,
                owner=request.user,
                tenant=tenant,
                template_id=data_in["template_id"],
                template_version=data_in["template_version"],
                start_date=data_in["start_date"],
                end_date=data_in["end_date"],
                rent_amount_minor=data_in["rent"]["amount_minor"],
                rent_currency="EGP",
                rent_exponent=2,
                offer_id=offer_id,
                offer_snapshot=copy.deepcopy(invitation.offer_snapshot),
            )
            invitation.lease = lease
            invitation.save(update_fields=["lease", "updated_at"])
            out = LeaseSerializer(lease, context={"request": request}).data
            _remember(
                request.user,
                "lease.create",
                data_in["request_key"],
                request.data,
                out,
                201,
            )
    except IntegrityError:
        replay = _replay(
            request.user, "lease.create", data_in["request_key"], request.data
        )
        if replay:
            return replay
        raise InvitationConflict("The accommodation already has a conflicting lease.")
    return Response(out, status=status.HTTP_201_CREATED)


def _get_authorized_lease(request, lease_id):
    lease = get_object_or_404(
        Lease.objects.select_related("property", "owner", "tenant"), id=lease_id
    )
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    return lease


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_detail(request, lease_id):
    return Response(
        LeaseSerializer(
            _get_authorized_lease(request, lease_id), context={"request": request}
        ).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_signing_session(request, lease_id):
    lease = _get_authorized_lease(request, lease_id)
    serializer = RevisionRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data["revision"] != lease.revision:
        return Response(
            {"message": "Lease revision conflict."}, status=status.HTTP_409_CONFLICT
        )
    replay = _replay(
        request.user,
        "lease.sign",
        serializer.validated_data["request_key"],
        request.data,
    )
    if replay:
        return replay
    expires = timezone.now() + timedelta(minutes=30)
    base = getattr(settings, "FEATURE_HOSTED_BASE_URL", "https://sokoun.app")
    with transaction.atomic():
        session = SigningSession.objects.create(
            lease=lease,
            signer=request.user,
            hosted_url=f"{base.rstrip('/')}/signing/{lease.id}",
            expires_at=expires,
        )
        if lease.status == Lease.Status.DRAFT:
            lease.status = Lease.Status.PENDING
            lease.revision += 1
            lease.save(update_fields=["status", "revision", "updated_at"])
        data = {
            "id": str(session.id),
            "subject_id": str(lease.id),
            "status": "pending",
            "hosted_url": session.hosted_url,
            "expires_at": expires.isoformat(),
        }
        _remember(
            request.user,
            "lease.sign",
            serializer.validated_data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_cancel(request, lease_id):
    lease = get_object_or_404(Lease, id=lease_id, owner=request.user)
    serializer = RevisionRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data["revision"] != lease.revision:
        return Response(
            {"message": "Lease revision conflict."}, status=status.HTTP_409_CONFLICT
        )
    if lease.status != Lease.Status.DRAFT:
        raise ValidationError("Only a draft lease can be cancelled.")
    replay = _replay(
        request.user,
        "lease.cancel",
        serializer.validated_data["request_key"],
        request.data,
    )
    if replay:
        return replay
    with transaction.atomic():
        lease.status = Lease.Status.CANCELLED
        lease.revision += 1
        lease.save(update_fields=["status", "revision", "updated_at"])
        data = {
            "id": str(lease.id),
            "subject_id": str(lease.id),
            "status": "cancelled",
            "revision": lease.revision,
        }
        _remember(
            request.user,
            "lease.cancel",
            serializer.validated_data["request_key"],
            request.data,
            data,
            200,
        )
    return Response(data)


def _invoice_queryset(user, workspace):
    if workspace == "owner":
        return RentInvoice.objects.filter(lease__owner=user)
    if workspace == "tenant":
        return RentInvoice.objects.filter(lease__tenant=user)
    raise ValidationError({"workspace": "Must be owner or tenant."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoices(request):
    RentInvoice.objects.filter(
        status=RentInvoice.Status.DUE, due_date__lt=timezone.localdate()
    ).update(status=RentInvoice.Status.OVERDUE)
    queryset = _invoice_queryset(
        request.user, request.query_params.get("workspace")
    ).select_related("lease", "lease__property")
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease__id=request.query_params["lease_id"])
    if request.query_params.get("status"):
        statuses = request.query_params["status"].split(",")
        invalid = set(statuses) - set(RentInvoice.Status.values)
        if invalid:
            raise ValidationError(
                {"status": f"Unsupported statuses: {', '.join(sorted(invalid))}"}
            )
        queryset = queryset.filter(status__in=statuses)
    ordering = request.query_params.get("ordering", "-created_at")
    if ordering not in {"due_date", "-due_date", "created_at", "-created_at"}:
        raise ValidationError({"ordering": "Unsupported ordering."})
    return _paginate(request, queryset.order_by(ordering, "id"), RentInvoiceSerializer)


def _get_authorized_invoice(request, invoice_id):
    invoice = get_object_or_404(
        RentInvoice.objects.select_related("lease", "lease__property"), id=invoice_id
    )
    if request.user not in (invoice.lease.owner, invoice.lease.tenant):
        raise NotFound()
    return invoice


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_detail(request, invoice_id):
    return Response(
        RentInvoiceSerializer(
            _get_authorized_invoice(request, invoice_id), context={"request": request}
        ).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_checkout(request, invoice_id):
    invoice = _get_authorized_invoice(request, invoice_id)
    if request.user != invoice.lease.tenant:
        raise PermissionDenied("Only the tenant can pay this invoice.")
    if str(request.data.get("invoice_id")) != str(invoice.id) or not request.data.get(
        "request_key"
    ):
        raise ValidationError(
            {
                "invoice_id": "The body invoice_id must match the path and request_key is required."
            }
        )
    if invoice.status not in {RentInvoice.Status.DUE, RentInvoice.Status.OVERDUE}:
        raise ValidationError("This invoice is not payable.")
    replay = _replay(
        request.user, "invoice.checkout", request.data["request_key"], request.data
    )
    if replay:
        return replay
    expires = timezone.now() + timedelta(minutes=15)
    base = getattr(settings, "FEATURE_HOSTED_BASE_URL", "https://sokoun.app")
    with transaction.atomic():
        session = CheckoutSession.objects.create(
            invoice=invoice,
            payer=request.user,
            hosted_url=f"{base.rstrip('/')}/payments/{invoice.id}",
            expires_at=expires,
        )
        data = {
            "id": str(session.id),
            "subject_id": str(invoice.id),
            "status": "pending",
            "hosted_url": session.hosted_url,
            "expires_at": expires.isoformat(),
            "amount": {
                "amount_minor": invoice.amount_minor,
                "currency": invoice.currency,
                "exponent": invoice.exponent,
            },
            "message": "",
        }
        _remember(
            request.user,
            "invoice.checkout",
            request.data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)
