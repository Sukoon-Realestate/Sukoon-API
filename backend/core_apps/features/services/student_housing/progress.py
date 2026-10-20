"""A read projection, not a second rental state machine."""


def next_step(plan, user, payload):
    own = next((row for row in payload["participants"] if row["is_current_user"]), None)
    if own and own["lease_id"]:
        return {
            "action": "rental",
            "waiting_for": "self",
            "reason": "rental_obligations",
        }
    if plan.status == "completed":
        return {"action": "history", "waiting_for": "", "reason": "plan_only_completed"}
    if (
        "roster_changed" in payload["blocking_reasons"]
        or "membership_revoked" in payload["blocking_reasons"]
    ):
        return {
            "action": "edit" if "edit" in payload["allowed_actions"] else "",
            "waiting_for": "coordinator",
            "reason": "roster_changed",
        }
    if own and own["status"] != "withdrawn":
        participant = plan.participants.get(user=user)
        if not participant.requirements:
            return {
                "action": "requirements",
                "waiting_for": "self",
                "reason": "missing_requirements",
            }
        if (
            own["reviewed_revision"] != plan.requirements_revision
            or participant.reviewed_digest != payload["digest"]
        ):
            return {
                "action": "review",
                "waiting_for": "self",
                "reason": "waiting_for_consent",
            }
    if payload["blocking_reasons"]:
        return {
            "action": "browse",
            "waiting_for": "participants",
            "reason": payload["blocking_reasons"][0],
        }
    if plan.groupprocess_set.exists():
        return {
            "action": "group",
            "waiting_for": "participants_and_owner",
            "reason": "independent_progress",
        }
    if payload["requests"]:
        return {
            "action": "requests",
            "waiting_for": "owner",
            "reason": "published_request",
        }
    return {"action": "browse", "waiting_for": "self", "reason": "ready_to_search"}
