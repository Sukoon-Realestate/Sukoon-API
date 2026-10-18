# Paymob callbacks

The callback receiver is separate from checkout creation and business fulfilment.
It does not mark rent, advertising or subscription invoices paid.

## Server configuration

Set these on the API service (values are kept out of this document):

```dotenv
PAYMOB_API_KEY=<account API key>
PAYMOB_PUBLIC_KEY=<test public key>
PAYMOB_SECRET_KEY=<test secret key>
PAYMOB_HMAC_SECRET=<account HMAC secret>
PAYMOB_INTEGRATION_ID=5991528
PAYMOB_WEBHOOK_URL=https://api.sukoon.rent/api/v1/payments/paymob/webhook/
PAYMOB_RETURN_URL=https://api.sukoon.rent/api/v1/payments/paymob/return/
```

Deploy the backend and apply its migration with the server's environment:

```sh
python manage.py migrate --settings=config.settings.production
```

In the Paymob **test** integration, save the webhook and return URLs above.
The URL settings are available for future checkout requests; setting them in
the environment does not update the Paymob dashboard automatically.

## Endpoint behavior

- `POST /api/v1/payments/paymob/webhook/?hmac=...`: accepts a JSON
  `TRANSACTION` envelope, verifies HMAC-SHA512 and the configured integration
  and EGP currency, then durably stores a minimal `PaymobCallbackEvent`.
  Repeated identical signed events are acknowledged without duplicate rows.
  Different states for the same transaction remain independent immutable facts;
  arrival order is not interpreted as payment-state order. Database failures
  return a server error so Paymob can retry.
- `GET /api/v1/payments/paymob/return/?...&hmac=...`: verifies the browser
  return and displays Paymob's reported status. It never modifies payment state.
  A return without valid signed parameters is rejected, so opening the bare
  URL in a browser is not a successful payment test.

No full callback, billing data or card data is stored. Stored flags and amounts
are signed provider facts, not proof that a particular Sukoon invoice was paid.
Invoice matching, amount validation against a server-created checkout, and
fulfilment must be implemented before enabling purchases in the app.

The callback receiver requires the HMAC secret and integration ID; otherwise it
returns 503. Other bad requests return 400, 403 or 415 as appropriate. The
receiver accepts only POST and the return page accepts only GET.

## Verification

```sh
pipenv run pytest core_apps/common/test_paymob_callbacks.py --ds=config.settings.test
```

Tests cover signed callbacks, tampering, duplicate deliveries, separate state
events, integration scoping, malformed payloads, missing configuration, and
display-only signed browser returns. They use synthetic credentials and make
no requests to Paymob.

Protocol references: [transaction callbacks](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/transaction-callbacks)
and [HMAC verification](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/hmac).
