# Area 3 — Rentals and Housing
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (`core_apps/features/` rental modules)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S3-N1 | low | maintainability | Long helper function in tenancy projection exceeds 500 lines, centralizing multiple serialization responsibilities | `core_apps/features/services/company/tenancy_projection.py:27` (535 lines) | Refactor projection payload into modular sub-serializers by component | verified |
| S3-N2 | medium | correctness | Lease termination transition relies on application-level checks rather than DB-level constraint preventing termination while dispute is open | `core_apps/features/model_parts/agreements.py:47` | Add model clean/constraint verification ensuring active dispute blocks premature closure | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| Monetary precision & minor units | pass | `core_apps/features/model_parts/agreements.py:95` (`rent_amount_minor` as `PositiveBigIntegerField`, explicit currency & exponent) | None |
| Agreement party exclusivity | pass | `core_apps/features/model_parts/agreements.py:130` (`CheckConstraint` `lease_exact_renter_party`: exact XOR between tenant and company) | None |
| Tenant and company workspace boundaries | pass | `core_apps/features/services/company/` (workspace isolation, scoped queries on corporate leases) | None |
| Digital signing authority & state transitions | pass | `core_apps/features/services/rental_lifecycle/` (verifies account verification, valid offer, atomic status updates) | None |
| Handover & condition evidence integrity | pass | `core_apps/features/model_parts/condition.py:15` (immutable condition photos, hash validation) | None |
| Dispute lifecycle & escrow freeze | pass | `core_apps/features/model_parts/operational_cases.py:40` (dispute blocks financial settlement until resolution) | None |
| Maintenance request authority | pass | `core_apps/features/model_parts/maintenance_changes.py:22` (restricted to active tenant of associated lease) | None |

