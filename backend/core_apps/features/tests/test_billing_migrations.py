"""Upgrade an existing paid-rent schema without rewriting financial history."""

import uuid
from datetime import date, timedelta
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


@pytest.mark.django_db(transaction=True)
def test_billing_upgrade_preserves_paid_rent_receipt_and_ledger():
    if connection.vendor != "postgresql":
        pytest.skip("Historical forward migration proof uses an isolated PostgreSQL schema.")
    # Start at the historical schema. Never reverse newer irreversible production
    # migrations or leave the shared test schema partially downgraded on failure.
    schema = "closure_migration_" + uuid.uuid4().hex
    quoted = connection.ops.quote_name(schema)
    with connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        original_path = cursor.fetchone()[0]
        cursor.execute(f"CREATE SCHEMA {quoted}")
        cursor.execute(f"SET search_path TO {quoted}")
    try:
        _assert_billing_forward_upgrade()
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('search_path', %s, false)", [original_path])
            cursor.execute(f"DROP SCHEMA {quoted} CASCADE")


def _assert_billing_forward_upgrade():
    executor = MigrationExecutor(connection)
    after = executor.loader.graph.leaf_nodes()
    before = [("features", "0017_renewal_effective_dates")]
    try:
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        model = lambda name: apps.get_model("features", name)
        user = apps.get_model("users", "User").objects.create(
            email="migration-history@example.test"
        )
        tenant = apps.get_model("users", "User").objects.create(
            email="migration-tenant@example.test"
        )
        governorate = apps.get_model("properties", "Governorate").objects.create(
            name="Migration"
        )
        city = apps.get_model("properties", "City").objects.create(
            name="Migration", governorate=governorate
        )
        kind = apps.get_model("properties", "PropertyType").objects.create(
            name="Migration", slug="migration"
        )
        prop = apps.get_model("properties", "Property").objects.create(
            owner=user,
            title="Existing rental history",
            governorate=governorate,
            city=city,
            property_type=kind,
        )
        lease = model("Lease").objects.create(
            property=prop,
            owner=user,
            tenant=tenant,
            template_id="historical",
            template_version="1",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            rent_amount_minor=12500,
            status="active",
        )
        invoice = model("RentInvoice").objects.create(
            lease=lease,
            reference="UPGRADE-PAID-RENT",
            due_date=date(2026, 1, 1),
            amount_minor=12500,
            applied_minor=12500,
            status="paid",
        )
        quote = model("PaymentQuote").objects.create(
            invoice=invoice,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            payer_amount_minor=12500,
            policy_version="existing-v1",
            fingerprint="f" * 64,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        attempt = model("PaymentAttempt").objects.create(
            invoice=invoice,
            payer=tenant,
            quote=quote,
            request_key=uuid.uuid4(),
            invoice_revision=1,
            policy_version="existing-v1",
            quote_fingerprint=quote.fingerprint,
            payment_status="captured",
            amount_minor=12500,
        )
        receipt = model("PaymentReceipt").objects.create(payment_attempt=attempt)
        invoice.receipt_id = receipt.id
        invoice.save(update_fields=["receipt_id"])
        ledger = model("LedgerTransaction").objects.create(
            reference="upgrade-history",
            kind="capture",
            lease=lease,
            invoice=invoice,
            payment_attempt=attempt,
        )
        for direction in ("debit", "credit"):
            model("LedgerEntry").objects.create(
                transaction=ledger,
                account=direction,
                direction=direction,
                amount_minor=12500,
            )
        identity = (invoice.id, invoice.pk, receipt.id, attempt.id, lease.id)
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(after)
    apps = executor.loader.project_state(after).apps
    invoice = apps.get_model("features", "RentInvoice").objects.get(id=identity[0])
    assert invoice.pk == identity[1] and invoice.purpose == "rent"
    assert invoice.payer_id is None and invoice.lease.id == identity[4]
    assert (
        invoice.status == "paid"
        and invoice.amount_minor == invoice.applied_minor == 12500
    )
    assert invoice.receipt_id == identity[2]
    assert invoice.payment_attempts.get().id == identity[3]
    entries = list(
        invoice.ledger_transactions.get().entries.values_list(
            "direction", "amount_minor"
        )
    )
    assert sorted(entries) == [("credit", 12500), ("debit", 12500)]
    assert set(
        apps.get_model("features", "PromotionOption").objects.values_list(
            "id", "duration_days"
        )
    ) == {("week", 7), ("month", 30)}
    assert not apps.get_model("features", "AccountSubscription").objects.exists()
