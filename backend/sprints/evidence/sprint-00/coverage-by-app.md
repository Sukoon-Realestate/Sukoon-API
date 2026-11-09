# Exercised statement coverage by app (application code only)

Excludes `*/migrations/*`, `*/tests/*`, `test_*.py`, `tests_*.py`, `conftest.py`. Measured with pytest-cov while the
full SQLite suite executed (not import-only). MVP mode deselects/gates deferred features, so its figure is lower by design.
Run date 2026-11-09; source `4d2556cf` + Sprint 00 changes.

| App | Statements | MVP mode | Restoration mode |
|---|---:|---:|---:|
| `admin_api` | 2,644 | 85% | 87% |
| `advertising` | 693 | 49% | 86% |
| `chat` | 4,705 | 76% | 89% |
| `common` | 2,806 | 58% | 59% |
| `features` | 38,707 | 46% | 87% |
| `notifications` | 1,210 | 88% | 89% |
| `profiles` | 1,347 | 90% | 92% |
| `properties` | 5,764 | 87% | 93% |
| `support` | 1,469 | 89% | 90% |
| `users` | 2,602 | 85% | 86% |
| `virtual_tours` | 3,080 | 79% | 79% |
| **Total** | 65,027 | **59.5%** | **86.1%** |
