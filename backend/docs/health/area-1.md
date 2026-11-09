# Area 1 — Identity
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (`core_apps/users/`, `core_apps/profiles/`)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S1-N1 | low | security | Session cookie duration in default/local settings does not mirror strict production session termination policy | `config/settings/local.py:45` | Document and synchronize session lifetime settings across test/staging configs | verified |
| S1-N2 | low | privacy | Initial user registration payload returns user account flags prior to identity document submission | `core_apps/users/serializers_parts/create_user_serializer.py:45` | Scope returned registration projection to minimal account identity fields | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| OTP expiry and attempt rate limits | pass | `core_apps/users/services/otp.py:25` (600s TTL, 60s cooldown, 5 attempts max, constant-time compare) | None |
| Email & identity verification | pass | `core_apps/users/models.py:78` (`is_email_verified`, `is_verified` required for sensitive business) | None |
| Session binding & instant revocation | pass | `core_apps/users/sessions.py:34` (`security_epoch`, `AuthSession.revoked_at`, active token invalidation) | None |
| Social identity binding | pass | `core_apps/users/models.py:112` (`SocialAccount` unique constraint on provider and uid) | None |
| Account closure blockers | pass | `core_apps/users/services/closure_blockers.py:18` (checks active leases, unpaid invoices, security disputes) | None |
| Staff TOTP & emergency recovery | pass | `core_apps/users/totp_models.py:20` (multi-step enrollment, hashed recovery codes, rate-limited verification) | None |
| Private identity-media authorization | pass | `core_apps/profiles/identity_media.py:45` (enforces `image/authenticated/`, SHA-256 filenames, rejects public URLs) | None |
| Profile & settings mass-assignment | pass | `core_apps/profiles/serializers_parts/user_settings_serializer.py:13` (`always_hide_mobile_number` locked read-only) | None |

