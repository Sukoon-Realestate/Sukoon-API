import pytest


@pytest.fixture(autouse=True)
def isolated_private_support_media(settings, tmp_path):
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = str(tmp_path / "private-support")


@pytest.fixture
def published_help(db):
    """Own test content; transactional tests may flush migration-seeded rows."""
    from core_apps.support.models import HelpArticle, HelpContact

    for workspace, slug in [("tenant", "visit-booking"), ("owner", "listing-property")]:
        HelpArticle.objects.update_or_create(
            slug=slug,
            defaults={
                "workspace": workspace,
                "active": True,
                "sort_order": 0,
                "question_en": "Synthetic help question",
                "question_ar": "سؤال اختبار",
                "answer_en": "Synthetic help answer",
                "answer_ar": "إجابة اختبار",
            },
        )
        HelpContact.objects.update_or_create(
            workspace=workspace,
            defaults={
                "active": True,
                "email": "support@example.invalid",
                "hours_en": "Daily synthetic hours",
                "hours_ar": "ساعات اختبار يومية",
            },
        )
