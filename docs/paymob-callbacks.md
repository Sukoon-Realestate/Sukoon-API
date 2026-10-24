# Paymob callbacks

The receiver stores verified callback facts. For an invoice-linked physical Paymob checkout, it then queries Paymob server-to-server and applies confirmed capture to the original invoice, allocation, receipt and ledger. The standalone landing-page test remains separate and grants no subscription benefits.

See [invoice-linked Paymob implementation and verification](qa/commerce-v1-2026-10-24/PAYMOB_IMPLEMENTATION.md) for the durable checkout/refund flows and operating commands.

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
PAYMOB_TEST_CHECKOUT_ENABLED=true
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
Invoice-linked physical payments match the provider order to a durable original attempt and independently query the provider. Amount, currency, integration, environment and original reference must all match before allocation. Unmatched landing-page callbacks remain stored facts and never mark an invoice paid. Digital subscriptions, advertisements and promotions cannot use this Paymob route.

The callback receiver requires the HMAC secret and integration ID; otherwise it
returns 503. Other bad requests return 400, 403 or 415 as appropriate. The
receiver accepts only POST and the return page accepts only GET.

## Landing-page test subscription

The Arabic and English landing pages include a test subscription card at
`#test-subscription`. Its form posts to
`/api/v1/payments/paymob/test-checkout/` and opens Paymob Unified Checkout.
The frontend uses `NEXT_PUBLIC_API_URL` if set, otherwise `https://api.sukoon.rent`.
No Paymob credentials are needed on the frontend. Native form navigation avoids
requiring browser CORS access to the checkout endpoint.

This is one **EGP 10** sandbox payment, not an automatically renewing subscription.
It does not create an account subscription or grant benefits. The backend sets the
price, currency, payment method and callback URLs; browser-provided overrides are
ignored. Billing details are validated and sent to Paymob without being stored
locally. Requests are throttled to five per minute per anonymous client IP.

Set `PAYMOB_TEST_CHECKOUT_ENABLED=true` on the API service to enable this flow.
It defaults to disabled and also requires test secret/public keys, an integration
ID, HMAC secret and HTTPS callback URLs. Live credentials are rejected even if
the enable flag remains set. Set the flag to `false` to disable test checkout.

Deploy the backend (including the callback migration) and landing page before
using the test form. Use Paymob test card data, never real card data, for this flow.

## Verification

```sh
pipenv run pytest core_apps/common/test_paymob_callbacks.py core_apps/common/test_paymob_checkout.py --ds=config.settings.test
```

Tests cover signed callbacks, tampering, duplicate deliveries, separate state
events, integration scoping, malformed payloads, missing configuration, and
display-only signed browser returns. They use synthetic credentials and make
no requests to Paymob.

Protocol references: [transaction callbacks](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/transaction-callbacks)
and [HMAC verification](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/hmac).
