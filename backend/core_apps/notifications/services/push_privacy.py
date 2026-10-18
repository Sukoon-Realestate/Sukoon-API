"""Push is an untrusted routing hint, not a private record projection."""

PUSH_TITLE = "سكون / Sokoun"
PUSH_BODY = "لديك تحديث جديد. افتح التطبيق لعرضه. / Open the app to view your update."
ROUTING_FIELDS = frozenset(
    {
        "action_type",
        "target_id",
        "workspace",
        "schema_version",
        "event_id",
        "notification_id",
        "notification_type",
        "property_id",
        "offer_id",
        "visit_id",
        "chat_id",
        "conversation_id",
        "lease_id",
        "invoice_id",
        "payment_attempt_id",
        "change_id",
        "change_kind",
        "group_id",
        "company_id",
        "item_id",
        "revision",
        "review_id",
        "opportunity_id",
        "section_id",
        "case_id",
        "request_id",
        "ticket_id",
        "subject_id",
        "subject_kind",
        "rental_lifecycle",
        "event_kind",
    }
)


def routing_data(data):
    return {
        key: value
        for key, value in (data or {}).items()
        if key in ROUTING_FIELDS and isinstance(value, (str, int, bool))
    }
