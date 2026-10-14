"""Reviewed assistant reply."""

from ..services.planning import money, offer_money


def assistant_reply(matches, context, filters, unresolved, extracted, language):
    ids = [str(prop.id) for prop, _ in matches]
    arabic = language == "ar"
    actions = [
        {"kind": "search", "title": "مراجعة البحث" if arabic else "Review search"}
    ]
    for prop, offers in matches:
        actions.append(
            {
                "kind": "property",
                "title": prop.title,
                "property_id": str(prop.id),
                "offer_id": (
                    context.get("offer_id", "")
                    if context.get("property_id") == str(prop.id)
                    and any(x["offer_id"] == context.get("offer_id") for x in offers)
                    else ""
                ),
            }
        )
    if len(ids) >= 2:
        actions.append(
            {
                "kind": "compare",
                "title": "مقارنة العقارات" if arabic else "Compare properties",
                "property_ids": ids,
            }
        )
    costs = []
    selected = next(
        (
            (prop, offer)
            for prop, offers in matches
            for offer in offers
            if str(prop.id) == context.get("property_id")
            and offer["offer_id"] == context.get("offer_id")
        ),
        None,
    )
    if selected:
        prop, selected_offer = selected
        if extracted and extracted["questions"]:
            actions.append(
                {
                    "kind": "messageDraft",
                    "title": (
                        "Review questions for the owner"
                        if language == "en"
                        else "مراجعة الأسئلة للمالك"
                    ),
                    "property_id": str(prop.id),
                    "offer_id": selected_offer["offer_id"],
                }
            )
        rent, deposit = offer_money(selected_offer)
        costs = [
            {
                "label": prop.title,
                "kind": "recurring",
                "period": selected_offer["terms"]["price_period"],
                "money": money(rent),
            },
            {
                "label": "التأمين" if arabic else "Deposit",
                "kind": "deposit",
                "period": "",
                "money": money(deposit),
            },
        ]
    reply = {
        "text": (
            "اقتراحات من بيانات العقارات المتاحة. راجع الفلاتر والشروط قبل المتابعة."
            if arabic
            else "Suggestions from available property records. Review filters and terms before continuing."
        ),
        "filters": filters,
        "unresolved_requirements": unresolved
        + [
            (
                "المتطلبات غير الظاهرة في الفلاتر لم يتم التحقق منها."
                if arabic
                else "Requirements not represented in the filters have not been verified."
            )
        ],
        "grounded_property_ids": ids,
        "actions": actions,
        "costs": costs,
        "provider": "gemini" if extracted is not None else "catalog_rules",
        "questions": extracted["questions"] if extracted else [],
        "grounded_offers": [
            {
                "property_id": str(prop.id),
                "offer_id": offer["offer_id"],
                "offer_revision": offer["offer_revision"],
                "terms": offer["terms"],
            }
            for prop, offers in matches
            for offer in offers
        ],
        "retain_history": False,
    }
    return reply
