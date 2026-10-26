"""Source workflow notices with current authority and no private planning inputs."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.users.models import User
from ..planning_models import PlanningEvent
from ..advanced_tender_models import (
    HousingTender,
    OwnerBid,
    PackageCandidate,
    TenderPackageRun,
    TenderBidClarification,
)
from ..housing_scenario_models import (
    HousingScenario,
    HousingScenarioRun,
    HousingScenarioDecision,
)
from ..transition_network_models import (
    MoveIntent,
    TransitionMatchRun,
    TransitionCandidate,
)

MODELS = {
    model._meta.label_lower: model
    for model in (
        HousingTender,
        OwnerBid,
        PackageCandidate,
        TenderPackageRun,
        TenderBidClarification,
        HousingScenario,
        HousingScenarioRun,
        HousingScenarioDecision,
        MoveIntent,
        TransitionMatchRun,
        TransitionCandidate,
    )
}
EVENT_KIND = "advanced_planning_updated"


def handles(item):
    return type(item) in MODELS.values()


def _tender(item):
    if isinstance(item, HousingTender):
        return item
    return item.bid.tender if isinstance(item, TenderBidClarification) else item.tender


def _scenario(item):
    return item if isinstance(item, HousingScenario) else item.scenario


def _student_scope(lease_id, user_id):
    from ..models import AcademicPlanParticipant

    return (
        "student"
        if AcademicPlanParticipant.objects.filter(
            lease_id=lease_id, user_id=user_id
        ).exists()
        else "individual"
    )


def context(item):
    """Return one explicit destination and the related recipient scopes."""
    if isinstance(
        item,
        (
            HousingTender,
            OwnerBid,
            PackageCandidate,
            TenderPackageRun,
            TenderBidClarification,
        ),
    ):
        tender = _tender(item)
        scope = "student" if tender.request.academic_plan_id else "individual"
        memberships = tender.group.memberships.filter(status="active")
        # Bids and their clarifications remain sealed to their owner and admins.
        if isinstance(item, (OwnerBid, TenderBidClarification, TenderPackageRun)):
            memberships = memberships.filter(role="admin")
        recipients = {
            row.user_id: scope
            for row in memberships
            if tender.member_access.get(str(row.user.id))
            == [str(row.id), row.joined_revision]
        }
        if isinstance(item, (OwnerBid, TenderBidClarification)):
            bid = item.bid if isinstance(item, TenderBidClarification) else item
            recipients[bid.owner_id] = "owner"
        elif isinstance(item, HousingTender):
            recipients.update(
                {pk: "owner" for pk in tender.bids.values_list("owner_id", flat=True)}
            )
        action, target = (
            ("open_tender_package", item.id)
            if isinstance(item, PackageCandidate)
            else ("open_housing_tender", tender.id)
        )
        return action, str(target), "", recipients
    if isinstance(item, (HousingScenario, HousingScenarioRun, HousingScenarioDecision)):
        scenario = _scenario(item)
        recipients = {scenario.request.coordinator_id: "company"}
        if isinstance(item, HousingScenarioDecision):
            recipients[item.approver.user_id] = "company"
            recipients[item.created_by_id] = "company"
        elif isinstance(item, HousingScenarioRun):
            recipients[item.created_by_id] = "company"
        action, target = (
            ("open_scenario_decision", item.id)
            if isinstance(item, HousingScenarioDecision)
            else ("open_housing_scenario", scenario.id)
        )
        return action, str(target), str(scenario.company.id), recipients
    if isinstance(item, TransitionCandidate):
        recipients = {
            row.user_id: _student_scope(row.intent.lease_id, row.user_id)
            for row in item.participants.select_related("intent")
        }
        return "open_move_candidate", str(item.id), "", recipients
    intent = item.intent if isinstance(item, TransitionMatchRun) else item
    return (
        "open_move_run" if isinstance(item, TransitionMatchRun) else "open_move_intent",
        str(item.id),
        "",
        {intent.user_id: _student_scope(intent.lease_id, intent.user_id)},
    )


def record(item, actor, operation):
    action, target, company_id, recipients = context(item)
    for recipient in User.objects.filter(pk__in=recipients, is_active=True):
        if actor and recipient.pk == actor.pk:
            continue
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"{operation}:{item._meta.label_lower}:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": action,
                    "target_id": target,
                    "event_kind": EVENT_KIND,
                    "source_model": item._meta.label_lower,
                    "source_id": str(item.id),
                    "revision": item.revision,
                    "change_kind": operation.split(".")[1],
                    "company_id": company_id,
                    "workspace": recipients[recipient.pk],
                    "schema_version": "1",
                }
            },
        )
    # A changed/withdrawn intent affects proposals shared with other participants.
    if isinstance(item, MoveIntent):
        for candidate in TransitionCandidate.objects.filter(
            participants__intent=item
        ).distinct():
            record(candidate, actor, f"transition.source_{item.id}_{item.revision}")


def authorize(event):
    data = event.destination
    model = MODELS.get(data.get("source_model"))
    if not model or data.get("event_kind") != EVENT_KIND:
        raise NotFound()
    item = get_object_or_404(model, id=data.get("source_id"))
    action, target, company_id, recipients = context(item)
    if (
        data.get("action_type"),
        data.get("target_id"),
        data.get("company_id", ""),
        data.get("workspace"),
    ) != (action, target, company_id, recipients.get(event.recipient_id)):
        raise NotFound()
    user = event.recipient
    if isinstance(
        item,
        (
            HousingTender,
            OwnerBid,
            PackageCandidate,
            TenderPackageRun,
            TenderBidClarification,
        ),
    ):
        from .housing_tenders.access import get_tender, get_package, admin
        from .housing_tenders.construction import get_run

        tender = get_tender(user, _tender(item).id)
        if isinstance(item, PackageCandidate):
            get_package(user, item.id)
        elif isinstance(item, TenderPackageRun):
            get_run(user, item.id)
        elif isinstance(item, (OwnerBid, TenderBidClarification)):
            bid = item.bid if isinstance(item, TenderBidClarification) else item
            if bid.owner_id != user.pk and not admin(user, tender):
                raise NotFound()
    elif isinstance(
        item, (HousingScenario, HousingScenarioRun, HousingScenarioDecision)
    ):
        from .housing_scenarios.access import scenario_for
        from .housing_scenarios.decisions import for_user

        if isinstance(item, HousingScenarioDecision):
            for_user(user, item.id)
        else:
            scenario_for(user, _scenario(item).id)
    else:
        from .transition_network.access import subject

        if subject(user, item.id) is None:
            raise NotFound()
    return {
        "title": "تحديث خطة السكن / Housing plan updated",
        "body": "افتح الحالة الحالية لمراجعة التغيير والخطوة المطلوبة. / Open the current state to review the change and required next step.",
    }
