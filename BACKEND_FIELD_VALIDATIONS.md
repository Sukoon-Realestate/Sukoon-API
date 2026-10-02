# Account field validation handoff

Updated: 2026-10-02. App: `apps/sokoun_app`.

## What the backend team should return

Please return a Markdown file named `BACKEND_VALIDATION_CONTRACT.md` containing
the actual server validation for every field below. Include required/optional
status, blank/null/omitted behavior, length and numeric limits, allowed formats,
normalization, uniqueness, cross-field rules, HTTP status codes, error response
examples, and valid/invalid examples. Mark rules that differ from this handoff.

This document records the mobile changes already implemented and requests the
missing server rules. It is not evidence that the backend currently enforces
these rules. After the backend returns its contract, the app can be aligned with
the confirmed policies and field-error response format.

Scope: registration, login, email verification and resend, password recovery,
Google sign-in, profile editing, and identity/KYC completion. Property, booking,
chat, and search forms are outside this account handoff.

All endpoint paths below are relative to `/api/v1/`.

## Changes implemented in the mobile app

| Field / flow | Previous behavior | Implemented behavior |
|---|---|---|
| First name, last name, full name | Nonempty and at most 50 UTF-16 code units; digits and markup could pass | Trim surrounding whitespace; 1–50 Unicode code points; Unicode letters and combining marks, with spaces, apostrophes (`'`, `’`), and hyphens between name parts; reject digits, markup, other symbols, and internal newlines |
| Registration and profile phone | Required only | Exactly 11 ASCII digits, matching `^01[0125][0-9]{8}$`; keep the leading zero |
| Email in registration, login, recovery | Partially anchored expression, 50-character cap; valid subdomains and domain hyphens could fail; invalid suffixes could pass | Check the entire trimmed address; local part at most 64 characters, total at most 254, domain labels at most 63; accept plus tags, subdomains, and domain hyphens; reject malformed dots, spaces, extra `@`, and trailing junk |
| Recovery email status indicator | Separate weaker email expression | Uses the same email syntax rule as submission |
| Registration password | At least 8 UTF-16 code units; whitespace-only values could pass; angle brackets rejected | At least 8 Unicode code points, with at least one non-whitespace character; preserve the exact password, including spaces and symbols such as `<` and `>` |
| Login password | Shared registration length and angle-bracket checks | Require a nonempty value only, then submit the exact existing credential; creation rules must not prevent an existing user from signing in |
| Password confirmation | Exact comparison duplicated across widgets | Shared required/exact-match check; no trimming |
| OTP | Shared validator accepted any string of at least 4 characters; screen checked only length 6 | Shared six-digit constant; exactly six ASCII digits, including leading zeroes; screen checks the actual value again before submitting |
| National ID | Screen checked 14 digits; data readiness checked only length 14 | Same 14-ASCII-digit syntax rule in the screen and data readiness; a display filename alone cannot satisfy new-account upload readiness |
| Validation messages | Several generic messages or raw keys | Specific English and Arabic messages for name, Egyptian mobile, OTP, national ID, and whitespace-only passwords |

The local Egyptian mobile assumption follows the app's `01xxxxxxxxx` hint and
existing account examples. The prefixes and lengths also match the
[NTRA numbering plan published by ITU](https://www.itu.int/dms_pub/itu-t/oth/02/02/T020200003E0004PDFE.pdf).
Backend: confirm whether the product accepts Egyptian local numbers only or also
international/country-code formats before adding normalization.

## Shared rules currently enforced by the forms

### Names

- Required after trimming surrounding whitespace; maximum 50 Unicode code points.
- A name part starts with a Unicode letter and may contain letters and combining
  marks. Parts may be joined by one or more ordinary spaces, one apostrophe, or
  one hyphen. No leading/trailing separators or repeated apostrophes/hyphens.
- Examples accepted: `محمد أحمد`, `مُحَمَّد`, `Élodie`, `O'Connor`, `Jean-Luc`, `李`.
- Examples rejected: `123`, `Ahmed1`, `<script>`, `Ahmed@Ali`, and 51-letter names.
- The app retains internal spaces and does not impose a two-letter minimum.

### Email

- Trim surrounding whitespace; preserve letter case in the outgoing payload.
- ASCII, unquoted dot-separated local part. Each segment follows this pattern:

  ```text
  [a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+
  ```

  No leading, trailing, or consecutive dots.
- Exactly one `@`. At least two domain labels; letters/digits with internal
  hyphens; no empty labels or leading/trailing label hyphens. The final label
  currently requires at least two ASCII letters.
- Limits: local part 64, each domain label 63, entire trimmed address 254.
- Accepted: `user+rent@sub.example-domain.co.uk`.
- Rejected: `user..name@example.com`, `user@example.com trailing`,
  `user@-example.com`, `user@example.com@other.com`.
- Quoted local parts, internationalized addresses, and punycode top-level
  domains are currently unsupported; backend must state whether these are needed.

### Phone, OTP, and national ID

| Value | Format | Normalization |
|---|---|---|
| `phone_number` | `^01[0125][0-9]{8}$` | Trim outer whitespace; send a string with its leading zero |
| `otp` | `^[0-9]{6}$` | No trimming, integer conversion, or case conversion |
| `national_id` | `^[0-9]{14}$` | Trim outer whitespace; send a string |

Phone and ID fields and the OTP input use ASCII digit input formatters.
The phone field currently accepts local digits only; `+20...`, `0020...`,
formatted numbers with separators, and Arabic-Indic digits are not supported as
typed formats. The backend contract should specify any desired normalization.
The syntax checks do not establish phone ownership or national-ID authenticity.

### Passwords

Registration keeps the existing eight-character minimum, now counted as Unicode
code points, rejects whitespace-only passwords, and compares confirmation
exactly. Login checks presence only. Neither flow trims, lowercases, normalizes,
or truncates passwords. No new maximum length or uppercase/digit/symbol quota
has been invented. Backend must supply its creation policy, maximum length and
length unit, password blocklist/similarity rules, and error messages.

## Endpoint field inventory

### Registration — `POST auth/users/` (JSON)

| Payload field | Type | Required in app | Mobile rule | Backend rules to confirm |
|---|---|---|---|---|
| `first_name` | String | Yes | Name rule; trim before sending | Server length, allowed characters |
| `last_name` | String | Yes | Name rule; trim before sending | Whether a single-name user may omit this field |
| `phone_number` | String | Yes | Local Egyptian mobile rule | Formats, normalization, uniqueness, ownership verification |
| `email` | String | Yes | Email rule; trim before sending | Case handling, uniqueness, verification, supported address formats |
| `password` | String | Yes | Registration password rule | Exact strength, similarity/blocklist and length policy |
| `re_password` | String | Yes | Exact match to `password` | Server equality check and confirmation error key |

Current request example:

```json
{
  "first_name": "Ahmed",
  "last_name": "Ali",
  "phone_number": "01012345678",
  "email": "ahmed+rent@example.com",
  "password": "example password",
  "re_password": "example password"
}
```

Registration sends these six fields. Identity documents are completed separately
by an authenticated account. The normal registration flow submits credentials,
verifies email through OTP, then returns to login. Owner/tenant workspace selection
does not add a `type` field to this request.

### Login — `POST auth/login/` (JSON)

| Field | Type | Required in app | Mobile rule | Server responsibility |
|---|---|---|---|---|
| `email` | String | Yes | Email rule; trim before sending | Account lookup/case policy |
| `password` | String | Yes | Nonempty only; preserve exact value | Authenticate, account status, email verification requirements, attempt limits |

Backend: provide examples for wrong credentials, an unverified account, a
disabled account, and throttling. Confirm the authentication-error status and
body so field failures are distinguishable from an expired session.

### Email verification — `POST auth/verify/` (JSON)

| Field | Type | Required | Mobile rule | Server responsibility |
|---|---|---|---|---|
| `email` | String | Yes | Reuse the trimmed email from registration | Bind code to account and verification purpose |
| `otp` | String | Yes | Exactly six ASCII digits | Correct code, expiration, single use, attempt limits, invalidation after resend |

### Resend OTP — `POST auth/resend-otp/` (JSON)

`email` is a required string, reused from registration. The UI currently has a
60-second resend countdown. Backend: confirm the actual cooldown, rate limits,
and retry metadata; client timers do not enforce server limits. Return whether a
new code replaces all previous codes and provide errors for already verified
accounts or blocked attempts.

### Password recovery — `POST auth/users/reset_password/` (JSON)

`email` is required, validated with the shared email rule and trimmed before
submission. Backend: specify the response for an unknown email, cooldowns,
throttling and link expiration. The mobile app requests a reset link; it does
not have a new-password form or call `auth/users/reset_password_confirm/`.
Provide the web reset-confirmation contract separately if that flow changes.

### Google sign-in — `POST auth/google/` (JSON)

`token` is the Google ID token supplied by the current sign-in service. The
button submits only when the service returns a nonempty token. Backend: confirm
this token type, verification of signature/issuer/audience/expiry, account linking
rules, and errors. Provider verification is server-side; the app does not treat
token syntax as proof of identity.

### Profile editing — `PATCH profiles/edit/` (multipart)

| Field | Type | Required in editable form | Mobile rule | Backend rules to confirm |
|---|---|---|---|---|
| `full_name` | String | Yes | Shared name rule, max 50; trim before sending | Full-name limit and permitted formats |
| `phone_number` | String | Yes | Local Egyptian mobile rule | Uniqueness excluding the current account; verification on change |
| `gender` | String | Yes | Selected `male` or `female`; unspecified blocks saving | Enum and blank/null behavior |
| `avatar` | File | No | Sent only when a new image is selected | Size, MIME types, decoded image validity, dimensions, removal behavior |

Email is read-only in the profile editor and is not submitted. City and birth
date are read-only display values and are not part of this edit payload.

The alternate existing `PATCH profiles/user/update/` serialization sends
`first_name`, `last_name`, `gender`, and `phone_number`. It splits `full_name` on
whitespace into the first word and remaining words. Backend: clarify whether
empty `last_name` is permitted on that route; the main editor uses
`profiles/edit/`. The alternate body does not send an avatar.

### KYC completion — `POST auth/complete-register/` (multipart, authenticated)

| Field | Type | Current existing-account behavior | Backend rules to confirm |
|---|---|---|---|
| `national_id` | String | May be omitted; if entered, exactly 14 ASCII digits | Required if missing in stored profile; uniqueness, ID/date/region checks and any age eligibility |
| `front_id_image` | File | May be omitted; sent if newly selected | Required if missing; allowed types, byte limit, dimensions and document checks |
| `back_id_image` | File | May be omitted; sent if newly selected | Required if missing; allowed types, byte limit, dimensions and document checks |
| `selfie_image` | File | May be omitted; sent if newly selected | Existing backend handoff calls it optional; confirm any conditional requirement and face/document matching |

Existing-account completion deliberately permits partial updates and omission
of already saved fields. No client upload byte-size, MIME, or dimension policy
is imposed until backend supplies it. The unused new-account KYC branch still
requires ID/front/back/selfie for readiness; actual upload objects must be
present. This branch is not the normal credential registration flow.

The app already consumes `registration_complete`, `verification_status`, and
`missing_fields` from completion responses. Preserve these keys or specify the
replacement contract. Document whether an unchanged or empty submission is a
valid status check, and which responses represent validation failure versus
incomplete registration.

Logout (`POST auth/logout/`) and account deletion (`DELETE auth/delete-account/`)
send no editable form fields. Backend remains responsible for authorization and
account/session restrictions.

## Validation-error response contract requested

Please provide actual HTTP status codes and complete response examples for each
endpoint. Include stable field keys, stable machine-readable error codes,
English/Arabic messages or translation codes, non-field errors, and retry
metadata for throttling. Include multiple errors on one field and multiple
invalid fields in one request. Never echo passwords or tokens in error bodies.

Example proposed shape for discussion, **not an implemented server contract**:

```json
{
  "message": "Please correct the highlighted fields.",
  "errors": {
    "phone_number": [
      {"code": "invalid_format", "message": "Enter a valid Egyptian mobile number."}
    ],
    "email": [
      {"code": "already_registered", "message": "This email is already registered."}
    ]
  }
}
```

The app currently displays local field errors and a general network error
message. It does not yet map an arbitrary server `errors` dictionary to field
controllers. That mapping should be implemented against the returned contract,
including any `detail`/`non_field_errors` format actually used by the server.

## Required backend reply format

Copy the following section for each endpoint; include every payload field,
even optional, provider-managed, and upload fields:

```markdown
## METHOD /api/v1/endpoint/
Authentication: ...
Content-Type: ...
Contract version / effective date: ...

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

Valid request example: ...
Invalid request examples and complete responses: ...
Success and validation/authentication/throttling HTTP statuses: ...
Upload limits (bytes, MIME, dimensions), if applicable: ...
Cooldown/expiry/attempt limit and retry metadata, if applicable: ...
Differences from BACKEND_FIELD_VALIDATIONS.md: ...
Rules the mobile app must add or revise: ...
```

## Implementation and verification

- Pure syntax checks: `packages/core/lib/core/helpers/account_input_rules.dart`.
- Localized validator adapters: `packages/core/lib/core/helpers/validators.dart`.
- Wiring: shared name/phone/password/confirmation widgets; registration, login,
  recovery, OTP and KYC screens; profile editor; KYC readiness model.
- Translation source: `packages/core/assets/translations/lang.json`; generated
  English, Arabic, and locale-key files updated through the repository generator.
- Regression coverage: `apps/sokoun_app/test/account_validation_test.dart` covers
  Unicode names and boundary lengths, complete email syntax, Egyptian mobile
  formats, exact OTP digits, password preservation and whitespace rejection,
  exact confirmation, localized field errors and KYC readiness.
- Live backend validation and provider/device integration are not verified by
  these client checks. Unknown server rules above remain pending the backend's
  Markdown reply.

Verified on 2026-10-02:

- 37 tests passed across account validation, login, password recovery, OTP
  contract/resend timer, profile flow, and KYC layout tests. The final test-fixture
  cleanup was also rechecked with all 10 new validation tests passing.
- Focused Dart analysis of the changed validators, widgets, auth feature,
  profile editor, and regression test: no issues.
- App-wide analysis reported unrelated existing warnings and deprecation notices
  outside these validation changes; it is not a clean app-wide analysis result.
- `dart format` and `git diff --check` passed for the validation work.

Reproduce the account test run from `apps/sokoun_app`:

```sh
flutter test --no-pub test/account_validation_test.dart \
  test/auth_login_test.dart test/auth_forgot_password_test.dart \
  test/auth_otp_contract_test.dart test/auth_resend_timer_test.dart \
  test/profile_flow_test.dart test/kyc_upload_documents_layout_test.dart
```

Tests used the locally installed Flutter SDK and its resolved dependencies.
SDK-pinned lockfile changes from the initial test run were restored; this change
does not require a dependency upgrade.
