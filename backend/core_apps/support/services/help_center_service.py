from django.db.models import Q
from core_apps.support.models import HelpArticle, HelpContact


def get_help_center_content(workspace="tenant", lang="ar"):
    workspace = "owner" if workspace.lower() == "owner" else "tenant"
    language = "en" if lang.lower() == "en" else "ar"
    contact = HelpContact.objects.filter(workspace=workspace, active=True).first()
    articles = list(
        HelpArticle.objects.filter(
            Q(workspace=workspace) | Q(workspace="both"), active=True
        )
    )
    return {
        "phone": contact.phone if contact else "",
        "email": contact.email if contact else "",
        "hours": getattr(contact, f"hours_{language}") if contact else "",
        "revision": max(
            [contact.revision if contact else 0, *[row.revision for row in articles]],
            default=0,
        ),
        "faqs": [
            {
                "id": row.slug,
                "question": getattr(row, f"question_{language}"),
                "answer": getattr(row, f"answer_{language}"),
                "revision": row.revision,
            }
            for row in articles
        ],
    }
