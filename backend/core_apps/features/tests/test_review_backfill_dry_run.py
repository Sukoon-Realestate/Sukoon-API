from io import StringIO
import pytest
from django.core.management import call_command
from core_apps.features.models import RentalReview, ReviewSection
from core_apps.features.tests.test_rental_phase3 import phase3_lease

pytestmark = pytest.mark.django_db


def test_legacy_import_dry_run_keeps_database_and_audience_unchanged(phase3_lease):
    _, tenant, lease = phase3_lease
    legacy = RentalReview.objects.create(
        lease=lease, author=tenant, rating=4, comment="Synthetic legacy review"
    )
    before = ReviewSection.objects.count()
    output = StringIO()
    call_command("migrate_legacy_reviews", dry_run=True, stdout=output)
    assert "Dry run" in output.getvalue()
    assert ReviewSection.objects.count() == before
    assert RentalReview.objects.filter(id=legacy.id).exists()
    call_command("migrate_legacy_reviews", stdout=StringIO())
    imported = ReviewSection.objects.get(legacy_id=legacy.id)
    assert (
        imported.verification_basis == "legacy_unverified"
        and imported.audience == "private"
    )
    call_command("migrate_legacy_reviews", stdout=StringIO())
    assert ReviewSection.objects.filter(legacy_id=legacy.id).count() == 1
