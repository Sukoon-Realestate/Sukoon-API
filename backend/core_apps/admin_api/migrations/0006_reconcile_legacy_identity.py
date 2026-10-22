"""Historical marker without an automatic global assurance cutover.

Schema deployment must not remove every existing verification flag. New
installations use review_legacy_identity: report, independent reviewer, explicit
account decision and current-state digest. Previously applied databases are not
automatically reversed; the report exposes their actual state for review.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("admin_api", "0005_kycsubmission_evidence_digest_and_more"),
        ("users", "0005_user_is_email_verified"),
        ("profiles", "0005_profile_phone_number"),
    ]
    operations = []
