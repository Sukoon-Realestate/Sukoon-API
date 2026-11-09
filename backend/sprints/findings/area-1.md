# Area 1 — Identity, accounts and profiles

**Scope:** 86 assigned production files, statically inventoried; selected authentication, account closure, social linking,
OTP, identity and profile-upload paths traced. See [source coverage](../SOURCE_INVENTORY.md) and [baseline](../BASELINE.md).
Most findings below are source-verified, not provider/concurrency experiments. Application code was not changed.
Priority/severity reflects proposed remediation order, not a claim of exploitation in production.

<a id="a1-01"></a>
## A1-01 — High — Unowned avatar references can become provider-deletion commands

**Evidence:** `core_apps/profiles/serializers_parts/update_profile_serializer.py:12-32,112-120` returns any non-data-image
string unchanged for the writable avatar. The Cloudinary field stores a parsed provider identity without a server-owned
upload receipt. `core_apps/users/services/account_closure.py:211-242` trusts the profile asset's public ID/type when
creating `AccountProfileErasureFile`; `services/closure_delivery.py:56-85` calls `cloudinary.uploader.destroy` on that ID.

**Trigger/impact:** a user assigns a parseable reference to another public asset in the same provider account as their
avatar. If their otherwise legitimate reviewed closure completes, that unrelated reference can be queued for deletion.
The closure reviewer verifies account obligations, not asset provenance. This is a cross-account asset-deletion path;
no provider deletion was executed during the audit.

**Task:** Sprint 01/02: accept actual uploads or owned server-issued media identities; record ownership/type/purpose at
upload, and recheck it before erasure. Plan safe treatment of existing untrusted references rather than destructively
deleting everything currently stored. Preserve immutable KYC evidence retention separately.

**Acceptance:** assigning another user's public ID/URL cannot attach it as owned or enqueue its deletion; a mocked
closure worker never destroys borrowed assets; valid owned avatars erase once; retained KYC snapshots remain accessible
only through their authorized evidence paths.

<a id="a1-02"></a>
## A1-02 — High — Inherited Djoser deletion bypasses reviewed closure

**Evidence:** `core_apps/users/rest_urls.py:7-77` inherits `UserViewSet`, registers all router actions and does not override
`destroy`/`me`. Installed Djoser `views.py:157-178` validates current password then deletes the instance; `me DELETE`
delegates to that action. The project's `finalize_response:58-73` converts upstream 204 to 200. The custom reviewed
closure routes and legacy delete guard do not intercept this inherited router path.

**Observed:** isolated `DELETE /api/v1/auth/users/me/` with the synthetic user's current password returned **200** and the
user no longer existed. This used a disposable SQLite test DB. No real account was accessed. Protected references may
instead raise `ProtectedError`; that does not make the unprotected case safe.

**Task:** Sprint 01: inventory self/detail/format aliases and deny or redirect all destructive inherited actions into
the approved closure workflow. Preserve legal/evidence retention, current authority, independent review and blockers.
Evaluate staff-targeted deletion aliases as well; do not rely on protected foreign keys as authorization.

**Acceptance:** no ordinary/admin alias physically deletes an account outside the approved process; with and without
protected records, return a defined response and preserve obligations/audit history. Authorized closure remains usable.

<a id="a1-03"></a>
## A1-03 — High — Social email auto-link preserves attacker-created local credentials

**Evidence:** `services/user_service.py:10-47` creates a local account/password before email possession is established.
`services/social_auth_service_parts/get_or_create_social_user.py:57-77` finds an existing account by a provider-verified
email, adds the social identity and marks email verified without retiring the existing usable password or sessions.

**Trigger/impact:** attacker pre-registers a victim email with an attacker-known password. Later the rightful owner signs
in with a verified Google/Apple identity for that email. Auto-link adopts the pre-created account while the original
credentials remain usable. Provider identity verification itself is present; the unsafe step is account adoption/linking.

**Task:** Sprint 01: define explicit authenticated linking for established accounts and a safe ownership-recovery/adoption
flow for unverified local accounts. Retire untrusted credentials and sessions before adopting a provider-verified identity;
handle concurrent linking under durable uniqueness/locks. Do not disable legitimate passwords blindly on every social login.

**Acceptance:** preregistration + rightful social login cannot leave the attacker authenticated; existing legitimately
verified-account linking, social UID collisions, inactive users and concurrent requests have explicit outcomes.

<a id="a1-04"></a>
## A1-04 — Medium — OTP attempts/consumption use non-atomic cache operations

**Evidence:** `services/otp_service.py:151-185` reads and overwrites the attempt counter outside a critical section;
`:197-210` locks the user only after a matching code has been read and deletes the cache record after the transaction.
Resend cooldown similarly uses get/set. Constant-time comparison, original deadline and security-epoch checks are present.

**Impact:** concurrent failed attempts can lose counter increments, and concurrent successful/resend requests can act on
the same cached state. This weakens the intended attempt/single-use/cooldown rules; it does not reveal the OTP or bypass
the need for a matching code by itself.

**Task:** Sprint 01/03: atomic compare/consume/increment on the shared cache or a durable locked challenge record, preserving
deadline and recovery epoch. **Acceptance:** parallel invalid requests cannot exceed the agreed attempt budget; one code
consumption wins; resend cannot race the cooldown or resurrect an old challenge; expiry/recovery remains fail-closed.

<a id="a1-05"></a>
## A1-05 — Medium — Identity submission loses the authenticated epoch before acquiring its lock

**Evidence:** `services/identity_submission.py:47-54` replaces the caller's user with a freshly locked row, checks only
active/closed state, then `:125-131` calls `execute_idempotent` without the original claims/expected epoch. The shared
idempotency guard therefore cannot compare the old authenticated identity with the new locked epoch; the no-key path
also lacks that recheck. `services/sessions.py:11-33,58-77` defines server-side revocation semantics.

**Impact:** an in-flight identity upload authenticated before `revoke_all` can resume after revocation and change evidence/
verification state while the account remains active. This is a concurrent revocation gap, not a general anonymous upload.

**Task:** Sprint 01/02: preserve original claims/expected epoch and revalidate after acquiring current user/profile locks,
including replay/no-key paths and before provider side effects. **Acceptance:** a PostgreSQL barrier test revoking between
authentication and locked submission rejects the old request without changing profile/KYC or creating ready media.

<a id="a1-06"></a>
## A1-06 — Medium — Legacy social token issuance does not use the bound-session issuer

**Evidence:** `users/views_parts/set_auth_cookies.py:125-141` delegates provider authentication to Djoser. The installed
default `djoser/social/token/jwt.py:1-9` uses `RefreshToken.for_user`; project settings do not replace that strategy with
`services/sessions.issue_refresh:37-55`. `validate_session:31-33` rejects unbound tokens after a revocation/bound-session gate.

**Impact:** configured legacy `/auth/o/<provider>/` sign-in can return newly issued tokens that the application rejects
after the account's first revocation. Normal custom Google/Apple adapters must be checked separately; no live provider
exchange was executed.

**Task:** Sprint 03/05: use one current-authority/bound-session issuance interface for every enabled login adapter, or
deliberately retire unsupported aliases. **Acceptance:** each configured adapter produces usable current-epoch sessions
after password change/recovery and cannot revive revoked sessions; cookie/refresh/body contracts stay documented.

<a id="a1-07"></a>
## A1-07 — Medium — Refresh mutates potentially immutable request data

**Evidence:** `views_parts/set_auth_cookies.py:95-105` selects the cookie/body refresh token then assigns directly to
`request.data['refresh']`. Form/multipart parsing can produce an immutable QueryDict, unlike JSON.

**Task:** Sprint 02/03: build a validated mutable command independently of the request, or explicitly restrict/document
accepted parsers. **Acceptance:** supported JSON/form/cookie refresh combinations have defined responses; malformed inputs
produce 400/415 rather than an immutable-data 500, and token rotation/revocation checks remain intact.

<a id="a1-08"></a>
## A1-08 — Medium hardening — Cookie JWT writes lack explicit CSRF verification

**Evidence:** `core_apps/common/cookie_auth.py:10-36` authenticates both header and cookie tokens without a cookie-specific
CSRF/origin check. DRF APIViews are CSRF-exempt unless their authentication policy enforces it. Base settings use
`COOKIE_SAMESITE='Lax'`, HttpOnly and configurable Secure; these protections are meaningful and must be preserved.

**Threat limit:** this is not proof that an arbitrary foreign website can make browsers attach Lax cookies on a cross-site
POST. Same-site hostile origins/subdomains, relaxed future cookie settings and login/session transitions need explicit
assessment. CORS alone is not the server-side authorization policy for unsafe cookie requests.

**Task:** Sprint 01 with client coordination: enforce an appropriate CSRF/origin policy for unsafe cookie-sourced auth,
keeping bearer-header mobile requests and separately authenticated provider callbacks distinct. **Acceptance:** supported
browser login/refresh/write flows succeed with required proof, missing/bad proof fails, and bearer/mobile contracts remain
usable. Verify actual deployed origin/proxy/cookie settings separately.

<a id="a1-09"></a>
## A1-09 — Medium performance — Registration performs email I/O inside account transaction

**Evidence:** `services/user_service.py:10,47` wraps registration in `transaction.atomic` and calls OTP delivery before
return. `services/otp_service.py:41-106,109-137` performs SMTP delivery in that call path.

**Task:** Sprint 04/05: durable delivery intent/outbox with post-commit dispatch and explicit uncertain-delivery/retry state,
not a fire-and-forget success claim. **Acceptance:** SMTP delay does not hold account locks; DB rollback sends no valid
orphan challenge; dispatch retries preserve one challenge deadline and the client's honest delivery state.

<a id="a1-10"></a>
## A1-10 — Architecture/cleanup — Consolidate identity entry points without removing protections

The source mixes CBVs with closure, TOTP, security and email-change function endpoints and legacy Djoser/social aliases.
Use Sprint 05's explicit route/method map and service boundaries. Preserve email possession versus independent KYC,
staff-factor recovery separation, sensitive-action proof, current authority, profile media proxy/version and revocation.
Stale comments and exported helpers are cleanup candidates only after alias/task/client review. No blanket identity
subsystem deletion is justified by this scan.
