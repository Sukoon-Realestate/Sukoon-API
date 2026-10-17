from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from ...company_models import Company, CompanyHousingRequest
from ...housing_scenario_models import HousingScenario, HousingScenarioRun
from ..company.access import member_for


def company_for(user, identifier, *, write=False, lock=False):
    query = Company.objects.select_for_update() if lock else Company.objects
    company = get_object_or_404(query, id=identifier)
    member = member_for(user, company)
    # Phase-one scenarios contain the complete request's private staff snapshot.
    # A package approver's narrower item authority does not authorize that roster.
    if not member.is_coordinator:
        raise NotFound()
    return company


def requests_for(user, company):
    member = member_for(user, company)
    query = CompanyHousingRequest.objects.filter(company=company)
    allowed = Q(pk__in=[])
    if member.is_coordinator:
        allowed |= Q(coordinator=user)
    return query.filter(allowed).distinct()


def request_for(user, identifier, *, write=False):
    request = get_object_or_404(CompanyHousingRequest, id=identifier)
    company = company_for(user, request.company.id, write=write)
    if write and request.coordinator_id != user.pk:
        raise NotFound()
    return get_object_or_404(requests_for(user, company), pk=request.pk)


def scenario_for(user, identifier, *, write=False, lock=False):
    query = HousingScenario.objects.select_related("request", "company")
    if lock:
        query = query.select_for_update(of=("self",))
    scenario = get_object_or_404(query, id=identifier)
    company_for(user, scenario.company.id, write=write, lock=lock)
    request_for(user, scenario.request.id, write=write)
    return scenario


def subject(user, identifier):
    from ...housing_scenario_models import (
        HousingScenarioDecision,
        HousingScenarioComparison,
    )
    from .decisions import for_user

    if HousingScenarioDecision.objects.filter(id=identifier).exists():
        return for_user(user, identifier)
    comparison = HousingScenarioComparison.objects.filter(id=identifier).first()
    if comparison:
        scenario_for(user, comparison.scenario.id)
        return comparison
    if HousingScenario.objects.filter(id=identifier).exists():
        return scenario_for(user, identifier)
    run = HousingScenarioRun.objects.filter(id=identifier).first()
    if run:
        scenario_for(user, run.scenario.id)
        return run
    return None


def actions(user, capability, subject_id=""):
    if capability not in {
        "corporate_housing_simulation",
        "corporate_housing_execution",
    }:
        return []
    if not subject_id:
        return ["read"]
    try:
        from ...housing_scenario_models import HousingScenarioDecision
        from .decisions import for_user, payload

        if HousingScenarioDecision.objects.filter(id=subject_id).exists():
            return payload(for_user(user, subject_id), user)["allowed_actions"]
        run = HousingScenarioRun.objects.filter(id=subject_id).first()
        if run:
            scenario_for(user, run.scenario.id)
            return (
                ["read", "cancel"] if run.state in {"queued", "running"} else ["read"]
            )
        if HousingScenario.objects.filter(id=subject_id).exists():
            scenario = scenario_for(user, subject_id)
            result = ["read"]
            member = member_for(user, scenario.company)
            if member.is_coordinator and scenario.request.coordinator_id == user.pk:
                result += [
                    "run",
                    "duplicate",
                    "request_decision",
                    "compare",
                    "validate",
                ]
            return result
        company_for(user, subject_id)
        member = member_for(user, Company.objects.get(id=subject_id))
        return ["read", "create"] if member.is_coordinator else ["read"]
    except (NotFound, Http404, PermissionDenied):
        return []
