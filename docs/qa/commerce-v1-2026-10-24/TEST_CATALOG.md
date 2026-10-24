# Sample packages for local testing

These are placeholder test prices approved for testing on 24 October 2026. All package names and descriptions explicitly say `[TEST]` / `[اختبار]`. Prices use EGP with two decimal places; yearly prices are twelve monthly payments, without an advertised discount or trial.

| Test package | Monthly EGP | Yearly EGP | Implemented test benefit / limit |
| --- | ---: | ---: | --- |
| Tenant Plus | 49 | 588 | Five active instant search alerts; daily alerts remain free. |
| Owner Pro | 99 | 1,188 | Owner analytics and CSV export for authorized properties; no numeric quota is configured. |
| Owner Business | 199 | 2,388 | The same implemented analytics/export benefit for now; a separate tier for testing catalog selection and pricing. No additional property/portfolio quota is promised. |
| Company Business | 499 | 5,988 | Organization-owned billing preview. No additional paid features, employee/unit quotas, signing authority or payment authority are granted. Company purchases remain disabled. |

`limit=null` is an unspecified numeric quota, not an “unlimited” marketing claim. Core rental, contract, payment, receipt, maintenance and support access remains unchanged. No access is granted merely by adding these catalog records.

## Create and use the local catalog

From `backend/`:

```sh
make seed-commerce-test-catalog
pipenv run python manage.py runserver --settings=config.settings.commerce_sandbox
```

The Make target migrates and seeds **`backend/commerce_sandbox.sqlite3`**, an isolated, gitignored local database. Existing development and production databases are untouched. Existing accounts are not copied to this separate database; use local QA accounts if running the API against it.

For an already migrated local/test database, run `seed_commerce_test_catalog` with its settings module. The command refuses production/staging runtimes, disabled QA settings or enabled store sales. It never contacts Paymob, Apple or Google.

There are eight stable plan UUIDs (four tiers, each monthly and yearly), sixteen **inactive sandbox-only placeholder SKUs**, and no live products. Repeating the command does not duplicate plans or bump unchanged revisions. Only its own stable test plan records are reset to sample values; unrelated plans, historical invoices, subscriptions, grants and feature enforcement settings are preserved.

Use the existing `subscription-plans/` and `subscriptions/current/` endpoints with `projection=mobile_v1` and the appropriate workspace/organization context. Company plans are only visible in an authorized company context. Placeholder product identifiers are not products registered with the app stores.

Run the focused checks with:

```sh
make test-commerce-test-catalog
```

Verified locally: all seven focused tests passed; the isolated catalog was migrated and seeded successfully. Django configuration/migration checks and focused lint passed. No production catalog or payment service was changed.
