"""Record blocked erasure requests without deleting obligations or inventing retention."""

from django.contrib.auth import get_user_model
from django.db import transaction
from core_apps.support.models import Ticket
from core_apps.support.services.ticket_service_parts.create_ticket import create_ticket


@transaction.atomic
def retain_closure_request(user):
    # Serialize retries and two-device requests on the existing account authority.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    reference = f"PRIVACY-{str(user.pk).replace('-', '')[:22]}"
    ticket = Ticket.objects.filter(reference=reference, user=user).first()
    if ticket:
        return ticket
    ticket = create_ticket(
        user=user,
        workspace="tenant",
        category=Ticket.Category.OTHER,
        subject="طلب مراجعة حذف الحساب والاحتفاظ بالسجلات",
        description=(
            "طلب المستخدم حذف حسابه. تعذر الحذف بسبب سجلات محمية. "
            "يلزم تحديد نطاق الاحتفاظ والحذف وفق السياسة المعتمدة. "
            "لم يتم حذف الحساب أو إلغاء أي عقد أو نقل أي التزام مالي."
        ),
    )
    ticket.reference = reference
    ticket.save(update_fields=["reference", "updated_at"])
    return ticket
