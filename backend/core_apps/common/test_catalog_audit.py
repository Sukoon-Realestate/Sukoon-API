import pytest
from core_apps.common.management.commands.audit_release_catalog import audit, https_destination
from core_apps.common.content_models import PublicContentPage
from core_apps.features.student_models import Campus

@pytest.mark.django_db
def test_report_does_not_mutate_or_invent_content():
    # Transactional tests can flush data-migration seeds before this test runs.
    # Create the exact invalid row; a missing fixture must not look like a pass.
    PublicContentPage.objects.update_or_create(pk="terms", defaults={
        "title_ar": "شروط اختبار", "title_en": "Test terms",
        "content_ar": "", "content_en": "Synthetic fixture only.", "active": True,
    })
    before = list(PublicContentPage.objects.values())
    result = audit()
    assert any(r["id"] == "terms" and "content_ar" in r["fields"] for r in result["invalid"])
    assert result["network_fetch"] is False
    assert list(PublicContentPage.objects.values()) == before
    assert "features.Campus" in result["missing"]

@pytest.mark.parametrize("url,valid", [("https://sukoon.rent/privacy", True), ("http://sukoon.rent", False), ("javascript:alert(1)", False), ("https://name:pass@example.org", False), ("", False)])
def test_link_validation_does_not_fetch_arbitrary_urls(url, valid):
    assert https_destination(url) == valid
