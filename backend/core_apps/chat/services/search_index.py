import re
import unicodedata
from urllib.parse import urlsplit

from django.db.models.signals import post_save
from django.dispatch import receiver

from core_apps.chat.models import Message
from core_apps.chat.models.search import ChatSearchDocument


def normalize(value):
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = "".join(c for c in value if unicodedata.category(c) != "Mn" and c != "ـ")
    return " ".join(value.translate(str.maketrans("أإآٱى", "ااااي")).split())


def links_in(value):
    result = []
    for match in re.findall(r"https?://[^\s<>\x00-\x1f]+", value or "", re.I):
        candidate = match.rstrip(".,;:!?،؛؟)]}\"'")
        try:
            uri = urlsplit(candidate)
            if (
                uri.scheme.lower() not in {"http", "https"}
                or not uri.hostname
                or uri.username
                or uri.password
            ):
                continue
        except ValueError:
            continue
        if candidate not in result and len(candidate) <= 2048:
            result.append(candidate)
    return result[:20]


def index_message(message):
    text = "" if message.deleted_at or message.kind == "system" else message.content
    ChatSearchDocument.objects.update_or_create(
        message=message,
        defaults={
            "body": normalize(text),
            "links": links_in(text),
            "revision": message.revision,
        },
    )


@receiver(post_save, sender=Message, dispatch_uid="chat_search_document")
def message_saved(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw or (
        update_fields is not None
        and not {"content", "deleted_at", "revision"}.intersection(update_fields)
    ):
        return
    index_message(instance)
