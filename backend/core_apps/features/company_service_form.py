"""Small operator form for existing canonical company proposals."""

from decimal import Decimal
from django import forms
from core_apps.users.models import User
from .models import RentInvoice, RentalEvidence
from .services.company import service_requests
from .services.company.tenancy_continuation_projection import choices
from .services.settlements import LINE_TYPES


class CompanyServiceFormFields(forms.Form):
    tenancy_revision = forms.IntegerField(required=False, widget=forms.HiddenInput)
    incoming_owner = forms.ModelChoiceField(
        User.objects.none(),
        required=False,
        help_text="Only the independently verified current property owner is eligible. Use a different assigned operator if that owner is an operator.",
    )
    financial_reviewer = forms.ModelChoiceField(User.objects.none(), required=False)
    correction_type = forms.ChoiceField(
        required=False,
        choices=[("", "Choose a correction")]
        + [(v, v.replace("_", " ")) for v in sorted(LINE_TYPES)],
    )
    correction_amount = forms.DecimalField(
        required=False,
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("-10000000000.00"),
        max_value=Decimal("10000000000.00"),
        help_text="EGP, one-time correction; existing funding and allocation rules apply.",
    )
    correction_description = forms.CharField(required=False, max_length=2000)
    correction_invoice = forms.ModelChoiceField(
        RentInvoice.objects.none(), required=False
    )
    correction_evidence = forms.ModelMultipleChoiceField(
        RentalEvidence.objects.none(), required=False
    )


FIELDS = tuple(CompanyServiceFormFields.base_fields)


def configure(form):
    case = form.instance
    if case.kind != service_requests.KIND:
        for name in FIELDS:
            form.fields[name].widget = forms.HiddenInput()
        return
    item = service_requests.tenancy(case)
    form.fields["decision_reason"] = forms.CharField(
        widget=forms.Textarea,
        required=False,
        max_length=2000,
        help_text="Explain the exact proposal and the evidence reviewed.",
    )
    current = choices(item, case.opened_by, {"owner", "payer"})
    form.fields["tenancy_revision"].initial = item.lease.revision
    form.fields["incoming_owner"].queryset = User.objects.filter(
        id__in=[v["id"] for v in current["ownership_candidates"]]
    ).exclude(pk=case.assigned_to_id)
    form.fields["financial_reviewer"].queryset = User.objects.filter(
        id__in=[v["id"] for v in current["financial_reviewers"]]
    ).exclude(pk=case.assigned_to_id)
    form.fields["correction_invoice"].queryset = RentInvoice.objects.filter(
        lease=case.lease
    )
    form.fields["correction_evidence"].queryset = RentalEvidence.objects.filter(
        lease=case.lease, malware_status="safe", deleted_at__isnull=True
    )
    hidden = (
        FIELDS[2:]
        if case.baseline["service_kind"] == "ownership_change"
        else ("incoming_owner",)
    )
    for name in hidden:
        form.fields[name].widget = forms.HiddenInput()


def proposal(form):
    data = form.cleaned_data
    if data.get("command_action") != "prepare_company_change":
        return None
    kind = form.instance.baseline.get("service_kind")
    required = ["tenancy_revision"] + (
        ["incoming_owner"]
        if kind == "ownership_change"
        else [
            "financial_reviewer",
            "correction_type",
            "correction_amount",
            "correction_description",
        ]
    )
    for name in required:
        if data.get(name) in (None, ""):
            form.add_error(name, "Required to prepare this exact proposal.")
    evidence = data.get("correction_evidence")
    if evidence is not None and len(evidence) > 5:
        form.add_error("correction_evidence", "Choose at most five clean files.")
    if form.errors:
        return None
    if kind == "ownership_change":
        return {"new_owner_id": str(data["incoming_owner"].id)}
    return {
        "financial_reviewer_id": str(data["financial_reviewer"].id),
        "lines": [
            {
                "id": str(data["request_key"]),
                "type": data["correction_type"],
                "description": data["correction_description"],
                "amount": {
                    "amount_minor": int(data["correction_amount"] * 100),
                    "currency": "EGP",
                    "exponent": 2,
                },
                "evidence_ids": [str(e.id) for e in evidence],
                **(
                    {"invoice_id": str(data["correction_invoice"].id)}
                    if data.get("correction_invoice")
                    else {}
                ),
            }
        ],
    }
