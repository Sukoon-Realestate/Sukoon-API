"""Company Responsibility command steps; typed adapters retain the HTTP boundary."""

from core_apps.features.services.company import responsibility_management as management


def action_post_authorize(*, action, actor, company_id, data, tenancy_id):
    item = management.get(actor, company_id, tenancy_id, lock=True)
    if action == "respond_change":
        management.authorize_decision(item, actor, data)
    return item
