"""Original text-send identities survive edits and deletion.

Rows predating receipts can recover from the first immutable edit. Already deleted
rows with no edit history cannot prove their original command and fail closed.
"""

import hashlib
import json


def text_fingerprint(content):
    payload = {
        "kind": "text",
        "content": content,
        "attachment_ids": [],
        "reply_to_message_id": None,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def preserve_original_send(message):
    if message.payload_fingerprint or message.kind != "text" or message.reply_to_id:
        return message.payload_fingerprint
    first_edit = message.edits.order_by("revision").first()
    if first_edit:
        original = first_edit.before
    elif message.deleted_at or message.edited_at:
        return ""
    else:
        original = message.content
    message.payload_fingerprint = text_fingerprint(original)
    message.save(update_fields=["payload_fingerprint"])
    return message.payload_fingerprint
