# Area 4 — Commerce
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (Payment, Billing, Paymob, Advertising)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S4-N1 | low | reliability | Webhook callback acknowledges signature before verifying downstream task queue capacity | `core_apps/common/paymob_views.py:51` | Ensure task queue failure propagates standard error response with exponential retry | verified |
| S4-N2 | low | security | Mock advertisement payment activation endpoint relies on settings check without explicit security alerting when non-production mode is active | `core_apps/advertising/services_parts/activate_with_mock_payment.py:63` | Add audit warning log whenever mock payment execution is triggered | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| Monetary precision & zero float rounding | pass | `core_apps/features/model_parts/payments.py:34` (all amounts in integer cents/minor units) | None |
| Webhook HMAC signature verification | pass | `core_apps/common/paymob_views.py:25` (`valid_signature` enforces HMAC-SHA512 over canonical values) | None |
| Webhook replay & duplicate delivery prevention | pass | `core_apps/common/paymob_views.py:51` (`PaymobCallbackEvent.objects.get_or_create` on signature) | None |
| Webhook currency & integration validation | pass | `core_apps/common/paymob_views.py:27` (strictly checks integration ID and `currency == "EGP"`) | None |
| Exactly-once capture / refund execution | pass | `core_apps/features/model_parts/payments.py:80` (idempotency key constraints, atomic state transitions) | None |
| Fake / live provider gates | pass | `core_apps/features/providers.py:102` (`fake_provider_available()` strictly checks `RENTAL_RUNTIME_ENVIRONMENT in {"development", "test", "staging"}`) | None |
| Advertising moderation & payment activation | pass | `core_apps/advertising/services_parts/activate_with_mock_payment.py:80` (requires `PENDING_PAYMENT`, valid owner, verified invoice) | None |
| Recipient retention & payout settlement | pass | `core_apps/features/services/settlements_parts/` (payout accounts locked to confirmed beneficiary) | None |

