from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from core_apps.chat.models import (
    AccountRestriction,
    RentalChatContext,
    ChatPolicyConsent,
    ChatPolicyNotice,
)

VERSION = "rental-chat-v1"
ACTIVE_RESTRICTIONS = ("pending_review", "permanent")
WARNING_AR = "لحماية حقوقك وحقوق الطرف الآخر وسكون، استكمل الاتفاق والعقد والدفع من خلال التطبيق. التعامل داخل سكون يساعد على توثيق التفاصيل ومتابعة النزاعات وتقليل مخاطر الاحتيال. تكرار محاولة إتمام التعامل خارج المنصة قد يؤدي لإيقاف الحساب للمراجعة."
WARNING_EN = "Keep the rental agreement, contract and payment in Sokoun to protect both parties and the platform. Documented transactions help resolve disputes and reduce fraud risks. Repeated attempts to complete the transaction outside Sokoun may restrict your account pending review."
BLOCKED_AR = "العقار موقوف مؤقتًا لمراجعة الالتزام بسياسات سكون"
BLOCKED_EN = "This property is temporarily unavailable while compliance with Sokoun policies is reviewed."


class PolicyDenied(APIException):
    status_code = 403

    def __init__(self, code, ar, en):
        from django.utils.translation import get_language

        super().__init__(
            {
                "code": code,
                "detail": ar if (get_language() or "ar").startswith("ar") else en,
            },
            code=code,
        )


def mode():
    value = getattr(settings, "CHAT_MODERATION_MODE", "off")
    return value if value in {"off", "shadow", "warn", "enforce"} else "off"


def restricted(user):
    return bool(
        user
        and user.is_authenticated
        and AccountRestriction.objects.filter(
            user=user, state__in=ACTIVE_RESTRICTIONS
        ).exists()
    )


def require_new_business(user, *, lock=False):
    if lock:
        from core_apps.users.models import User

        User.objects.select_for_update().get(pk=user.pk)
    if restricted(user):
        raise PolicyDenied(
            "account_restricted",
            "التعاملات الجديدة متوقفة لحين مراجعة الحساب. يمكنك متابعة التزاماتك القائمة وتقديم اعتراض.",
            "New transactions are restricted. You can access existing obligations and submit an appeal.",
        )


def visible_properties(qs):
    return qs.exclude(
        owner_id__in=AccountRestriction.objects.filter(
            state__in=ACTIVE_RESTRICTIONS
        ).values("user_id")
    )


@transaction.atomic
def attach_context(conversation, actor, data=None):
    from core_apps.properties.models import Property
    from core_apps.users.models import User
    from core_apps.chat.models import Conversation

    if not data:
        current = RentalChatContext.objects.filter(conversation=conversation).first()
        if current or mode() == "off":
            return current
    people = list(conversation.participants.order_by("pk"))
    list(
        User.objects.select_for_update()
        .filter(pk__in=[p.pk for p in people])
        .order_by("pk")
    )
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    if conversation.kind != "direct" or actor.pk not in [p.pk for p in people]:
        raise ValidationError("Rental context requires a direct participant.")
    existing = RentalChatContext.objects.filter(conversation=conversation).first()
    if not data:
        if existing or mode() == "off":
            return existing
        # Legacy clients cannot bypass rental policy by omitting UI context.
        owners = list(
            Property.objects.filter(owner__in=people, retired_at__isnull=True)
            .order_by("owner_id")
            .values_list("owner_id", flat=True)
            .distinct()
        )
        if not owners:
            return None
        return RentalChatContext.objects.create(
            conversation=conversation, owner_id=owners[0], source="owner_inventory"
        )
    if not isinstance(data, dict) or set(data) - {
        "property_id",
        "owner_id",
        "offer_id",
        "offer_revision",
    }:
        raise ValidationError("Invalid rental context.")
    prop = None
    if data.get("property_id"):
        from uuid import UUID

        try:
            identity = UUID(str(data["property_id"]))
        except (ValueError, TypeError):
            raise ValidationError("Invalid property identity.")
        prop = Property.objects.filter(
            id=identity, retired_at__isnull=True, owner__in=people
        ).first()
        if not prop:
            raise ValidationError("The property does not belong to this conversation.")
        owner = prop.owner
    else:
        owner = next(
            (p for p in people if str(p.id) == str(data.get("owner_id"))), None
        )
        if (
            not owner
            or not Property.objects.filter(
                owner=owner, retired_at__isnull=True
            ).exists()
        ):
            raise ValidationError("Choose an owner with an existing property.")
    if data.get("offer_id") or data.get("offer_revision"):
        if not prop:
            raise ValidationError("An offer requires a property.")
        from core_apps.features.services.tenancy_invitations import (
            resolve_offer_snapshot,
        )

        resolve_offer_snapshot(prop, data.get("offer_id"), data.get("offer_revision"))
    require_new_business(owner)
    require_new_business(actor)
    context = existing or RentalChatContext.objects.create(
        conversation=conversation, owner=owner
    )
    if prop:
        context.properties.add(prop)
    return context


def enrolled(conversation):
    return (
        conversation.kind == "direct"
        and RentalChatContext.objects.filter(conversation=conversation).exists()
    )


def require_send(conversation, user):
    require_new_business(user)
    if not enrolled(conversation) or mode() not in {"warn", "enforce"}:
        return
    if (
        not ChatPolicyConsent.objects.filter(user=user, version=VERSION).exists()
        or ChatPolicyNotice.objects.filter(
            user=user, kind="warning", acknowledged_at__isnull=True
        ).exists()
    ):
        raise PolicyDenied(
            "policy_ack_required",
            "راجع تنبيه حماية المحادثة وأكده قبل إرسال رسالة جديدة.",
            "Review and acknowledge the chat protection notice before sending another message.",
        )


def account_payload(user):
    records = list(
        AccountRestriction.objects.filter(user=user, state__in=ACTIVE_RESTRICTIONS)
        .select_related("case")
        .order_by("created_at")
    )
    return {
        "restricted": bool(records),
        "state": (
            "permanent"
            if any(r.state == "permanent" for r in records)
            else "pending_review" if records else "active"
        ),
        "case_ids": [str(r.case.id) for r in records],
        "can_appeal": bool(records),
        "can_manage_existing_obligations": True,
    }


def projection(conversation, user):
    active = enrolled(conversation) and mode() in {"warn", "enforce"}
    notice = (
        ChatPolicyNotice.objects.filter(
            user=user, kind="warning", acknowledged_at__isnull=True
        )
        .select_related("case")
        .order_by("created_at")
        .first()
        if active
        else None
    )
    from django.utils.translation import get_language

    ar = (get_language() or "ar").startswith("ar")
    reminder = (
        ChatPolicyNotice.objects.filter(
            conversation=conversation,
            user=user,
            kind="off_topic",
            created_at__gt=timezone.now() - timedelta(days=1),
        ).exists()
        if active
        else False
    )
    return {
        "enabled": active,
        "off_topic_reminder": reminder,
        "policy_version": VERSION,
        "consent_required": active
        and not ChatPolicyConsent.objects.filter(user=user, version=VERSION).exists(),
        "account": account_payload(user),
        "notice": (
            {
                "id": str(notice.id),
                "case_id": str(notice.case.id),
                "kind": notice.kind,
                "message": WARNING_AR if ar else WARNING_EN,
            }
            if notice
            else None
        ),
    }
