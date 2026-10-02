# App validation changes

Updated: 2026-10-02. App: `apps/sokoun_app`.

This implementation follows [BACKEND_VALIDATION_CONTRACT.md](BACKEND_VALIDATION_CONTRACT.md),
version `v1.0.0`. It replaces the earlier handoff's proposed rules with the
returned backend contract.

## Single validation reference

All client input rules, limits, formatters, and validation messages are owned by
`packages/core/lib/core/helpers/validators.dart` through the `Validators` class.
The separate `AccountInputRules` helper has been removed. Form callbacks,
submission guards, and model readiness getters delegate to `Validators`.

Shared form infrastructure still controls when to validate and where to display
errors. Parsing API responses, formatting displayed values, and tracking whether
data changed are separate from field validation.

## Contract alignment

| Field or flow | Implemented validation and normalization |
|---|---|
| Registration first and last names | Required; trim; maximum 50 Unicode code points; Unicode letters and combining marks, spaces, apostrophes, and hyphens. At least one letter is required. Digits, markup, and internal newlines are rejected. No extra rule restricts separator position or repetition. |
| Profile full name | Optional; trim; the same character rules, with a 100-code-point maximum. |
| Email | Required; whole-address validation; maximum 254 characters and 64 in the local part. Dot-separated local parts, Django-compatible quoted local parts, subdomains, Unicode/punycode domains, and address literals are supported. Trim and lowercase before submission. |
| Registration and profile phone | Optional. Accept local `^01[0125][0-9]{8}$` and international `^\+201[0125][0-9]{8}$`. Strip ordinary spaces, parentheses, and hyphens before validation and submission. The field preserves `+` when typed. |
| Registration password and confirmation | At least eight Unicode code points, non-whitespace. Confirmation must exactly match. Passwords retain their original case, spaces, and symbols. |
| Login password | Require a nonempty value; preserve the exact credential without applying registration strength requirements. |
| OTP | Trim; exactly six ASCII digits; preserve leading zeroes. Input length, formatting, completion state, submission checks, and request serialization use the shared rules. |
| Profile gender | Optional; blank, `male`, or `female`. |
| Birth date | Optional; strict `YYYY-MM-DD` calendar date, including leap-year checks. No age restriction is added. The existing registration/profile UI has no editable birth-date field, so no new field or payload entry is introduced. |
| Google token | Require a nonblank token; trim the submitted token. Provider verification remains on the server. |
| National ID | Optional; when supplied, trim and require exactly 14 ASCII digits. |
| Avatar | Optional; JPEG, PNG, WEBP, or GIF; maximum 10 MiB (10,485,760 bytes). |
| KYC images | Each optional; JPEG, PNG, or WEBP; maximum 10 MiB per image. Partial and empty submissions remain possible so the server can report completion status and missing fields. |

Image checks inspect actual file signatures and decode image content, rather
than trusting a filename or extension. They reject unreadable, empty, corrupt,
unsupported, and oversized files. Checks run after picking an image and again
before submitting. No image dimension limit is imposed because the contract
specifies none. The contract's “10 MB” limit is implemented as `10 * 1024 * 1024`
bytes; the exact boundary and boundary-plus-one are covered by tests.

## Other centralized app rules

The existing property, search, booking, rating, and chat validation policies also
now delegate to `Validators`: finite coordinate bounds, required property fields,
positive numeric values, price range ordering, photo metadata and counts,
property video duration, visit day/time selection, ratings from one through five,
and nonblank chat messages with the existing 5,000-character limit. Their rules
remain separate from the account contract because that contract does not specify
these feature endpoints.

ASCII and localized-digit input formatting are owned by `Validators`; the
app's `LocalizedDigitsFormatter` is a forwarding adapter.

## Responses and server responsibilities

Password recovery now treats `204 No Content` as success even when the response
contains no JSON envelope. A real HTTP regression test covers this response.

Server validation errors continue to display the contract's flattened
`{"message": "..."}` text. The contract supplies no per-field error dictionary,
so the app does not invent a field-error mapping.

Email uniqueness, Django password blocklists and similarity checks, credential
verification, Google token verification, phone/ID authenticity, OTP expiry and
attempt limits, rate limiting, and KYC completion status remain server-owned.
The existing 60-second resend countdown is consistent with the contract; the
backend enforces the actual cooldown.

English and Arabic validation messages are generated from
`packages/core/assets/translations/lang.json` using the repository's string
generator.

## Validation error messages

`Validators` now returns English and Arabic messages for the actual failed rule:
missing values, unsupported characters or formats, length limits, number ranges,
password confirmation, and upload failures. Required-name and required-email
messages identify what to enter; excessive lengths report the applicable limit
separately from syntax errors. OTP and national ID errors explicitly request
ASCII digits from 0 to 9. Phone errors show accepted local and international
examples.

Limits in messages are substituted from validator constants or method arguments,
including 50/100-character names, email limits, passwords, OTPs, document size,
and video duration. Messages no longer undergo a second localization lookup.
Google sign-in reports an invalid token through the existing error toast, and
the KYC upload hint now states JPEG/PNG/WEBP up to the shared 10 MB limit.

## Verification

- The preceding contract implementation passed 163 tests across the 20 suites
  below, including account boundaries,
  request normalization, localized fields, uploads, empty password-reset
  responses, and the affected feature flows.
- After the message update, 48 tests passed across account validation, login,
  recovery, OTP/resend, Google sign-in, profile, KYC layout, and video suites.
  Shared-field tests check missing values, formats, length limits, and corrections
  in both English and Arabic. All 52 validator translation keys exist in both locales.
- Focused Dart analysis of the changed source and test files: no issues.
- App-wide analysis reports six existing warnings outside these changes.
- Formatting and whitespace checks are performed on the implementation files.
- Tests use Flutter 3.35.1 / Dart 3.9.0, matching the resolved workspace SDK.
- Live backend behavior and image-picker/Google provider integration on devices
  have not been exercised by these tests.

From `apps/sokoun_app`, using the matching Flutter SDK:

```sh
flutter test --no-pub \
  test/account_validation_test.dart test/auth_login_test.dart \
  test/auth_forgot_password_test.dart test/auth_otp_contract_test.dart \
  test/auth_resend_timer_test.dart test/auth_google_login_test.dart \
  test/profile_flow_test.dart test/kyc_upload_documents_layout_test.dart \
  test/dio_cookie_session_test.dart test/chat_thread_cubit_test.dart \
  test/chat_flow_test.dart test/owner_properties_flow_test.dart \
  test/property_location_picker_test.dart test/tenant_visits_flow_test.dart \
  test/book_visit_time_picker_test.dart \
  test/collection_request_body_contract_test.dart \
  test/property_video_playback_test.dart test/property_photo_save_test.dart \
  test/search_history_test.dart test/ui_controls_test.dart
```
