"""Student eligibility and backwards-compatible search imports."""

from ..rental_lifecycle.discovery import (
    SearchContext,
    filter_properties,
    matching_offers,
)  # noqa: F401


def eligibility(prop, selection, actor, dates=None):
    """Explain this actor's current eligibility without disclosing private proofs."""
    from django.utils import timezone
    from .policies import policy_for, policy_payload
    from .profiles import enrollment

    policy = policy_for(prop, selection["offer_id"])
    if not policy:
        return {"state": "open", "policy": None}
    if (
        policy.expires_at <= timezone.now()
        or policy.offer_revision != selection["offer_revision"]
    ):
        state = "policy_changed"
    elif (
        dates
        and dates.get("starts_on")
        and (
            dates["starts_on"] < policy.starts_on
            or dates["ends_on_exclusive"] > policy.ends_on_exclusive
        )
    ):
        state = "dates_unavailable"
    elif actor is not None and actor.is_authenticated and actor.pk == prop.owner_id:
        state = "owner_review"
    elif policy.eligibility == "open":
        state = "open"
    elif actor is None or not actor.is_authenticated:
        state = "verification_required"
    else:
        state = (
            "eligible"
            if enrollment(
                actor, allow_admission=policy.eligibility == "admission_or_enrollment"
            )
            else "verification_required"
        )
    return {"state": state, "policy": policy_payload(policy)}
