"""Push is an untrusted routing hint, not a private record projection."""

PUSH_TITLE = "سكون / Sokoun"
PUSH_BODY = "لديك تحديث جديد. افتح التطبيق لعرضه. / Open the app to view your update."
ROUTING_FIELDS = frozenset(
    {
        "action_type",
        "scope",
        "message_id",
        "recipient_id",
        "membership_period",
        "chat_actions_version",
        "target_id",
        "workspace",
        "presentation_workspace",
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
        "company_role",
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


def presentation_context(data):
    data = dict(data or {})
    action = str(data.get('action_type', ''))
    if data.get('scope') == 'account':
        data.pop('workspace', None)
        data.pop('presentation_workspace', None)
        return data
    explicit = data.get('workspace') or data.get('presentation_workspace')
    if explicit in {'tenant', 'individual', 'owner', 'student', 'company'}:
        data['presentation_workspace'] = 'individual' if explicit == 'tenant' else explicit
    elif data.get('academic_plan_id') or data.get('student_plan_id'):
        data['presentation_workspace'] = 'student'
    elif action.startswith('open_company_'):
        data['presentation_workspace'] = 'company'
    return data


def routing_data(data):
    return {
        key: value
        for key, value in presentation_context(data).items()
        if key in ROUTING_FIELDS and isinstance(value, (str, int, bool))
    }
