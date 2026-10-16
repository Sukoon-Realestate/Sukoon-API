# ADR: physical accommodation allocated through unit/date uniqueness

Status: implemented locally; production cutover requires the migration/backfill audit.

The existing `RentalInventoryDayLock` is retained. Each property has canonical `RentalInventoryUnit` records keyed by bed, room-without-beds, or a whole-property sentinel when no internal rooms exist. A room expands to all its beds; a room group is the union; an entire property expands to every current physical unit. Therefore incompatible offer IDs cannot hide shared physical accommodation.

The database backstop is a unique `(unit, stay_on)` constraint for mapped rows. A partial `(property, offer_id, stay_on)` constraint protects unmapped historical rows until reviewed conversion. Presence of a day row blocks allocation; expiry is an explicit locked command, not an index predicate depending on wall time. This is the daily-granularity equivalent of interval exclusion for the existing date-based tenancy contract.

Transactions lock actor for idempotent commands, then property, then relevant lease/proposal/group/hold, then units/day rows and finance sources. Every competing allocation path uses the property root, while the unique constraint catches any missed concurrent unit/day collision. Half-open date intervals permit adjacent stays unless turnover adds blocked days. Transferring a free hold to its agreement reassigns the same rows.

A live or unresolved payment prevents blind hold expiry. Known overdue possession also blocks a new occupant. A signed renewal can continue only the same tenancy root, owner, tenant, selection and adjacent dates. Its child inherits existing possession; applied predecessor agreements no longer act as a second occupancy authority. New parties and unrelated offers do not qualify for this exception.

Topology edits are rejected while any allocation rows exist. This is intentionally conservative, including historical occupied rows; structural migration needs an explicit reviewed procedure. Unknown historical selections remain blocked and are reported by `reconcile_rental_inventory`. No conflicting rows are silently deleted.

Tradeoffs: daily rows grow with units × dates; maximum booking length and batched inserts bound new commands. This does not support hourly accommodation. A later interval model would require an audited migration of the current authority, not a parallel reservation store.

Database design references: [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) and [Django transaction row locking](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-for-update). PostgreSQL tests use separate connections for competing holds/refunds; sequential API tests alone are not concurrency evidence.
