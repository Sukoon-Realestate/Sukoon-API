# Sprint 11 — Remove proven obsolete code and misleading production fixtures

**Outcome:** a smaller, clearer codebase without breaking active clients, migrations, registration or test seams.
**Evidence:** A2-10, A4-09/A4-10, A5-14, A6-11/A6-12; cleanup candidates in area reports.

## Classification before deletion

| Class | Action |
|---|---|
| Verified active fixture/fabricated output | Replace with real state or explicit unavailable/no-history contract |
| Reference-verified obsolete private helper | Remove definition and stale imports; test actual replacement path |
| Public facade/import compatibility | Retain explicit supported exports or coordinate deprecation; do not mass-autofix |
| Fake/staging/test provider and seed tool | Keep if used, clearly gated/isolated; demonstrate it cannot enable fake production success |
| Legacy routed upgrade/empty response | Client contract decision; deprecate with telemetry/rollout, not an unannounced deletion |
| Unreferenced by text search only | Candidate, not proven dead; check dynamic consumers/registries/import strings |

## Concrete cleanup

- Remove literal historical advertising fixture restoration and solid-color fabricated-artwork fallback from request
  serving. Use an explicit audited repair command with verified source bytes if historical repair remains necessary.
- Remove invented owner acceptance/rating numbers through the canonical aggregate/no-history contract.
- Check obsolete `_notify_recipients`/`_broadcast_new_message` helpers and the unrouted GroupPreferencesAPIView against
  supported callers; retain durable outbox/current preferences behavior. Evaluate old PropertyMediaMixin helpers with
  their tests/external consumers before removal.
- Reduce copied unused import lists in stable facade/parts modules, duplicate reexports, unused locals and redefinitions.
  Replace blanket F401 suppression with explicit exports/narrow reviewed exceptions.
- Consolidate cohesive repeated pure helpers and policy registries. Do not add more one-function files merely to lower
  function length; review whole use cases for readable names, clear inputs and obvious ownership.
- Remove/update obsolete comments/docs describing unsupported architecture, dummy statistics or nonexistent environment
  paths. Keep migration history, durable task names and rollout compatibility fields until their retirement is proven safe.

## Acceptance

- Each deletion has evidence of no required route/import/task/signal/admin/migration/test/client consumer and the replacement
  behavior is covered. Uncertain candidates stay labeled; no assertion that every unused-looking function is dead.
- GETs never fabricate customer artwork or repair storage/database fixtures. Missing media remains unavailable until repaired.
- No required fake/test adapters, explicit upgrade responses, supported exports or historical migrations disappear.
- Scoped lint/import/type checks and contract/query regressions pass. The prior 2,476 F401 warnings are classified/resolved,
  not blindly equated with 2,476 safe deletions or hidden by a global ignore.
