from django.db import models


class PaymobCallbackEvent(models.Model):
    """Immutable verified payment facts awaiting business reconciliation.

    Store only signed payment fields; never the full callback, card or billing data.
    Separate state notifications for one transaction remain separate events.
    """

    signature = models.CharField(max_length=128, unique=True)
    transaction_id = models.CharField(max_length=18, db_index=True)
    order_id = models.CharField(max_length=18, db_index=True)
    integration_id = models.CharField(max_length=18)
    amount_cents = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    reported_status = models.CharField(max_length=16)
    flags = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
