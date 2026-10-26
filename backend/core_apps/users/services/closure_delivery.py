"""Durable delivery/erasure work; none of these retries executes a business command."""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from ..models import AccountClosureNotice, AccountProfileErasureFile


def deliver(limit=100):
    count = 0
    for identity in list(
        AccountClosureNotice.objects.filter(email_sent_at__isnull=True, attempts__lt=5)
        .order_by("created_at")
        .values_list("pk", flat=True)[:limit]
    ):
        with transaction.atomic():
            item = (
                AccountClosureNotice.objects.select_for_update()
                .select_related("decision__request")
                .get(pk=identity)
            )
            if item.email_sent_at or item.attempts >= 5:
                continue
            decision = item.decision
            completed = decision.action == "completed"
            body = (
                (
                    "اكتمل إغلاق حسابك. حُفظت السجلات اللازمة للالتزامات السابقة وفق صلاحياتها. / "
                    "Your account is closed. Required records of previous obligations remain protected."
                )
                if completed
                else (
                    "تم تحديث طلب حذف الحساب. يمكنك متابعة الحالة والسجل من إعدادات الحساب. / "
                    "Your closure request changed. Review account settings for its current status and history."
                )
            )
            item.attempts += 1
            try:
                accepted = send_mail(
                    "متابعة طلب حذف الحساب / Account closure",
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [item.email_to],
                    fail_silently=False,
                )
            except Exception:
                accepted = 0
            if accepted == 1:
                item.email_sent_at = timezone.now()
                count += 1
            item.save()
    return count


def erase_files(limit=100):
    import cloudinary.uploader

    count = 0
    for identity in list(
        AccountProfileErasureFile.objects.filter(deleted_at__isnull=True)
        .order_by("updated_at")
        .values_list("pk", flat=True)[:limit]
    ):
        with transaction.atomic():
            item = AccountProfileErasureFile.objects.select_for_update().get(
                pk=identity
            )
            if item.deleted_at:
                continue
            item.attempts += 1
            try:
                result = cloudinary.uploader.destroy(
                    item.public_id,
                    resource_type="image",
                    type=item.storage_type,
                    invalidate=True,
                )
            except Exception:
                result = {}
            if result.get("result") in {"ok", "not found"}:
                item.deleted_at = timezone.now()
                item.public_id = ""
                count += 1
            item.save()
    return count
