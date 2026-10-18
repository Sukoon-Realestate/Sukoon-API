# Chat and private-document repair rollout

This rollout separates additive database changes from the code that reads the new columns. The inspected App Platform startup runs Gunicorn and does not run migrations. Deploying the new models before their columns exist would break ordinary queries.

## Scope and existing data

The live read-only preflight found nine direct conversations, no duplicated exact two-person pairs, and zero `RentalDocument` rows. PostgreSQL reports version 17.11. These are bounded observations at the inspection time, not a full integrity certification.

- `chat.0009_conversation_direct_pair_key` adds a nullable unique pair identity. Existing conversations are retained; the service later adopts the earliest exact two-person historical conversation under ordered account locks. It does not merge or delete messages.
- `features.0050_alter_rentaldocument_options_and_more` adds typed-source, failure and media fields, plus uniqueness for nonempty source references.
- `features.0051_retire_mislabeled_document_artifacts` retains historical bytes but marks untyped, non-statement READY artifacts failed. The inspected database has zero matching rows. Do not reinterpret a ledger export as a signed contract.
- No identity migration, policy approval, financial reconciliation or worker activation is part of these commands.

## Deployment sequence

1. Validate the exact code-and-schema candidate. The isolated PostgreSQL run passed 117 tests, including concurrent opposite-direction direct-chat creation, retained duplicate history, private-document bytes, digest, session/logout/expiry/revocation/recovery gates, rental closure and existing chat HTTP/socket/group tests. Two native audio cases were skipped because Android/iOS recording fixtures were not provided.
2. Publish the three migration files while retaining the previous runtime models. Capture an encrypted private backup of only the two affected tables and verify the downloaded archive before any live migration.
3. Inspect the live migration plan. Apply only `python manage.py migrate chat 0009 --noinput` and `python manage.py migrate features 0051 --noinput`. Recheck applied migration identities, the new columns and row counts. Do not run unrestricted `migrate` against unrelated pending work.
4. Publish the tested model/service/view/worker changes after the schema is present. Keep the existing recovery gate and provider configuration.
5. Verify ordinary chat reuse and authorization with the two QA users. Invalid private-document download tokens must fail. Real signed-artifact retrieval and worker execution remain separate dependencies.

If a code rollout fails, return to the preceding compatible code while retaining the additive columns. Schema reversal would remove those new fields and their later data and therefore needs a separate review; it is not an automatic rollback step. The private table archive is a recovery artifact, not permission to overwrite newer live rows.

Executed deployment identities, migration output and live check results are recorded in the app repository's deployment and capability work log.
