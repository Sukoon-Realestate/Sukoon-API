# Architecture and readability target

The requested destination is explicit CBV transport adapters, cohesive domain services and readable helpers. An existing
function endpoint is a target mismatch, not automatically a security defect. An `@api_view`-generated class is still a
function-based implementation for this migration. Wrapping a 200-line function in `post()` alone does not meet the goal.

## Boundaries

| Layer | Owns | Must avoid |
|---|---|---|
| `urls` | Stable paths, names, converters and explicit `.as_view()` mappings | Domain state decisions or duplicated policy |
| CBV | Parse input, invoke typed validation/current authority, call command/selector, format response | Stateful business workflows, provider logic, repeated per-row reads |
| Command serializer | Complete field/container schema, bounds and supported types | Performing irreversible side effects during validation |
| Domain command/service | Invariants, current authorization, transaction/lock order, revisions, receipts and durable side effects | Importing HTTP view modules, trusting a stale request-user snapshot |
| Selector/read service | Scoped querysets, annotations/prefetch/batched authority facts, stable pagination | Full-history work before paging or hidden per-object provider calls |
| Projection/response serializer | Format prepared data and explicitly bounded nested data | Implicit SQL/remote I/O for every field or item |
| Pure helper | Small deterministic transformations with a clear domain name | Catch-all utility modules and implicit global context |
| Model | Data integrity and durable constraints | Transport-specific responses or unchecked external execution |
| Worker/provider adapter | Claimed retryable I/O, bounded work, proof and reconciliation | New external action from a GET or a transaction retry |

Use DRF generic CBVs for ordinary resource reads and APIView for explicit commands/stateful workflows. Raw signed provider
callbacks may use Django `View` to preserve exact body/HMAC semantics; binary streaming endpoints retain their parser and
credential model. Channels consumers are not HTTP views and are not converted into APIViews.

Prefer a cohesive domain module/package when it tells one clear story. Do not add a service class, selector layer or file
for a trivial pure expression without a concrete readability/testability benefit. Do not keep a large mixed use case hidden
inside an arbitrarily named `*_parts` file. Keep stable public model/import identities needed by migrations and clients.

## Migration order for each route family

1. Inventory every alias, HTTP method, callback, serializer, auth/permission/capability, throttle, parser, renderer, status,
   header, streaming behavior, locale, replay and expected-revision rule.
2. Characterize valid behavior and meaningful negative cases. Approve bug/security behavior changes separately from the
   mechanical conversion; capture old/new client expectations where a security fix intentionally changes the contract.
3. Extract a command or prepared read projection while the existing route still delegates to it. Make current authority,
   locks, transaction boundaries, receipts and `on_commit` behavior explicit.
4. Replace the routed function with a thin named class using the same domain service. Remove the old route implementation
   only when no caller or alias still depends on it. Run parity and query/payload gates.
5. Remove redundant compatibility plumbing after checking imports, routers, task names, signals, admin and migrations.

Company authorization is currently keyed by function module/name in `features/services/company/role_routes.py`. Planning,
company and tour decorators also add validation, capability, rendering and privacy headers. Replace those responsibilities
with explicit class/method policies before changing callable identity. A generic `get`/`post` name cannot substitute for
the existing policy key. Never improve speed by dropping fresh revocation/participant checks.

## Quality standard

- Human-readable names and one clear responsibility per use-case method; branch complexity and repeated policy facts are
  review signals. A line-count threshold alone is not acceptance.
- Complete typed command boundaries, explicit response shapes, deterministic error status and useful correlation logs
  without credentials, document bytes or unnecessary personal data.
- Narrow exception handling where recovery is understood; provider uncertainty remains durable/reconcilable rather than
  being swallowed or treated as success.
- No blanket unused-import suppression. Public facade exports use explicit supported exports/aliases; remove other unused
  imports only after checking side effects and registries. Do not delete a function solely because text search finds no caller.
- New dependencies and schema changes are small reviewed changes with compatibility and forward-migration plans.

Update the repository guidance in a documentation change: the backend `CLAUDE.md` still says function-only views,
`apps/` and `Project.settings`, which conflict with the actual project and this user-approved CBV target.

## Architecture acceptance

The resolved API inventory has zero project-owned decorated/plain function callbacks after migration, and no class is a
shell around the unchanged mixed HTTP/domain implementation. All route aliases and supported methods remain accounted
for. Domain services do not import view modules. Representative read models operate on prepared bounded data; command
tests exercise state changes independently of HTTP. Client contracts, privacy, current authority and recovery behavior
remain covered. Framework-generated/admin internals are identified rather than mechanically rewritten.
