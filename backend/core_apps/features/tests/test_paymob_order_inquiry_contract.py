import io
import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from core_apps.features.services import paymob_client as client


@pytest.mark.parametrize(
    "detail,allowed,absent",
    [
        ({"detail": "Transaction Not Found"}, True, True),
        ({"detail": "Not found."}, True, False),
        ({"detail": "Transaction Not Found"}, False, False),
    ],
)
def test_only_explicit_inquiry_absence_is_recognized(detail, allowed, absent):
    error = HTTPError(
        "https://accept.paymob.com/test",
        404,
        "Not Found",
        {},
        io.BytesIO(json.dumps(detail).encode()),
    )
    with patch.object(client, "credentials_ready", return_value=True), patch.object(
        client, "build_opener"
    ) as opener:
        opener.return_value.open.side_effect = error
        with pytest.raises(client.PaymobUnavailable) as result:
            client.transport("/test", allow_no_transaction=allowed)
    assert isinstance(result.value, client.PaymobNoTransaction) is absent


@pytest.mark.parametrize(
    "paid,missing,valid", [(0, True, True), (1000, True, False), (0, False, False)]
)
def test_live_order_shape_without_history_requires_verified_empty_inquiry(
    paid, missing, valid
):
    payment = SimpleNamespace(
        order_id="123",
        reference="original",
        attempt=SimpleNamespace(amount_minor=1000, currency="EGP"),
    )
    order = {
        "id": 123,
        "merchant_order_id": "original",
        "amount_cents": 1000,
        "currency": "EGP",
        "paid_amount_cents": paid,
    }
    with patch.object(
        client, "transport", side_effect=[{"token": "server-token"}, order]
    ), patch.object(
        client,
        "inquiry",
        side_effect=client.PaymobNoTransaction if missing else client.PaymobUnavailable,
    ):
        if valid:
            assert client.order_transactions(payment) == []
        else:
            with pytest.raises(client.PaymobUnavailable):
                client.order_transactions(payment)
