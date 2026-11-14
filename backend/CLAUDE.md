# CLAUDE.md — Sukoon Backend API

---

For model/migration/endpoint/serializer work, prefer the `django-feature` skill.

## Project conventions (always honor)
- Use the `Makefile` targets. The environment is built from `Pipfile.lock` (Python 3.11, includes
  `pillow-heif`): `pipenv install`, or a hash-checked `backend/.venv` as described in the
  `django-feature` skill. There is no `./Venv/`.
- Settings live in `config/settings/` (`base.py` + one module per environment). Tests use
  `config.settings.test` (pytest.ini); PostgreSQL tests use `config.settings.postgres_test` with disposable
  `TEST_POSTGRES_*` values. Deployed env comes from the repo-root `.env`/platform; never read or edit it for tests.
- Apps live in `core_apps/<app>/` (urls → thin views → serializers → `services/`).
- Architecture target (user-approved; see `sprints/ARCHITECTURE.md`): new and converted HTTP endpoints are
  explicit class-based views; domain services own transactions, locks, authority and side effects. The existing
  526 `@api_view` routes are migration debt converted by sprints 05–10 — do not add new `@api_view` functions
  and do not change route names/aliases/contracts during conversion.
- DRF endpoints use cookie/SimpleJWT auth (`core_apps.common.cookie_auth`), django-filter and the configured
  pagination/renderer. Admin is Django admin plus the `admin_api` staff API (no django-unfold).
- The MVP release switch (`SUKOON_MVP`, default true) gates deferred routes in `core_apps/common/mvp_scope.py`;
  run both `make test-baseline-mvp` and `make test-baseline-restoration` for cross-cutting changes.
- Regenerate `sprints/ROUTE_MATRIX.md` (`make route-matrix`) whenever routes change.
- Never alter `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/`, `media/` or production state to make tests pass.

## Identity adapters after Sprint 05

Identity URLs use explicit `.as_view()` classes (including closure, challenges,
TOTP and email-change aliases). Preserve `http_method_names`, `name` (OPTIONS
metadata), authentication, renderers and throttles when editing these adapters.
Keep each supported HTTP method explicit and retain existing error precedence.

- Registration aliases share `services.user_service.register_user`; Djoser's
  `user_registered` signal sends its OTP once (`dispatch_otp=False` in its serializer).
- Login/verification/social flows share `services.sessions.issue_refresh` and
  `issue_token_pair`. Refresh rotation uses `refresh_bound_session` under the
  account lock; never mint an unbound token in a view or provider strategy.
- Password adapters delegate to `services.passwords` and revoke sessions in the
  same transaction as the password write. Recovery links revalidate after locking.
- Session commands use `services.session_management`; closure uses
  `services.account_closure`. All destructive aliases preserve object permissions and return the reviewed-closure
  requirement, including Djoser's `me` and detail/format variants.
- `users.selectors` and `profiles.selectors` prepare reads and select private media
  by account ownership and exact asset version. Card expiry commands live in
  `profiles.identity_expiry`, with reusable input validation in `expiry_inputs`.

Example: validate a command in an adapter, call a named domain command, then use
`Response(data, status=code, headers=response_headers(replayed))`. The command owns
locks, fresh authority, revision checks, receipts and committed side effects.
Run `make test-sprint05-identity CYCLE_SETTINGS=<scratch_settings>` using a fresh
scratch database/storage root; see `sprints/evidence/sprint-05/README.md`.

### Bounded identity reads (Sprint 05 completion)

Preserve legacy collection bodies when no pagination controls are supplied.
`bounded=true` opts sessions, staff identity lists and recovery review queues into
page metadata, defaults to 20 rows, and caps `page_size` at 100. `page` and
`page_size` also opt those collections in. Invalid/out-of-range controls are 400;
out-of-range collection pages are 404. Closure queues keep their established
pagination envelope.

`bounded=true` also bounds nested closure/recovery history to 5 rows by default;
`history_page`/`history_page_size` can be used independently (maximum 20 history
rows per parent). Closure summary pages both its outer account history and its
current request's history. Page metadata is added only when these controls are
used. Omitted controls preserve complete legacy histories by the user's explicit
compatibility decision. Do not silently truncate history or invent an API-wide
payload cap for that legacy mode.

Closure read projections use `closure_reads.prepare_projections`; recovery reads
use `recovery_reads.authorized_rows` before pagination and prepared history. Never
use a request-scoped read fact to authorize a later mutation: command-time
`_can_review`, current factor/session and account locks remain authoritative.
All provider names/subjects and malformed command containers fail as client
errors; social verification must continue checking signature, issuer, audience
and expiry before linking or issuing a bound session.

Inherited Djoser update and activation actions use `services.inherited_accounts`.
Update must replace the cached serializer target with its locked current row and
recheck object permission against the fresh actor. Activation revalidates the
link after acquiring the account lock and refuses closed accounts. Native and
inherited password changes recheck current session/account authority inside the
mutation transaction. Do not reintroduce a stale `User.save()` in an adapter.


## Property and tour adapters after Sprint 06

Property/appointment URLs and tour/capture/review/viewer APIs use explicit method
classes. Keep their legacy names, methods, renderers, errors and aliases. Tour
transport policies live in `virtual_tours.http`; credential/byte endpoints disable
account authentication and keep `RawPartParser` streaming. Upload parsing must
remain lazy until grant/resource authority has been checked.

`virtual_tours.operations.mutate` accepts explicit actor/claims/key/body/ETag and
passes its locked current actor to authoring/capture commands. Always execute
those command bodies through that durable receipt boundary. Listing/image and
appointment services own their account/listing/appointment locks, revisions,
replay and committed notifications. Do not move state transitions into adapters.
`public_access.public_properties` is the canonical property publication predicate;
tour sessions and signed bytes recheck it on every public access. Private previews
retain separate current owner/reviewer checks.

Tour review/owner/capture selectors prepare page data and batch security/retry/
revision facts. Capture reads retain 20 sessions, 20 jobs per session and two
selected revisions per job; review pages retain 20 rows. Complete legacy review
histories remain compatible and data-dependent. Do not silently truncate them.
Use `make test-sprint06-properties-tours CYCLE_SETTINGS=<scratch_settings>`;
PostgreSQL processes must each use a distinct disposable TEST database name.
See `sprints/evidence/sprint-06/README.md` for reproduction and limits.

## Housing adapters after Sprint 07

Non-commerce housing routes use explicit `.as_view()` classes and per-method
`ActionPolicy` metadata in `features.http`. Company policies must supply the
stable resource/action pair consumed by `services.company.role_routes`;
`get`/`post` and class names are never company authorization identities.
Keep current resource/membership/mandate authority in command services, including
receipt replay. Planning policies retain capability-before-body-validation,
typed/untyped body rules, Django validation translation and success privacy.

Personal handover/maintenance state changes live in `services.handover_commands`
and `services.personal_maintenance`; transport supplies typed command data,
original receipt data and authentication claims. Company tenancy commands live
in `services.company.tenancy_commands`, with prepared read sections in
`tenancy_reads`. Read facts have one response's lifetime and never grant command
or byte access. `tenancy_access.visible` and `contract_access.visible` accept
validated scope constraints before authority evaluation. Compatible complete
legacy histories remain data-dependent; do not silently truncate them.

Sprint 07 remains partially accepted: remaining domain extraction, full positive
route/method/role/workspace matrices and hard family performance/retention
criteria are listed in `sprints/evidence/sprint-07/README.md`. Explicit classes
alone do not satisfy the service architecture target. Reproduce scoped checks
with `make test-sprint07-housing CYCLE_SETTINGS=<isolated_settings>
BASELINE_OUT=<scratch_directory>` and the ledger with `make sprint07-coverage`.

## Communication adapters after Sprint 09

Chat, notification and support routes resolve to explicit CBVs. Chat's 14 former
productivity/forwarding/mention/OS-action functions retain their methods, OPTIONS
names and transport policies. Do not restore decorated functions or obsolete
pre-outbox broadcast helpers. `services.commands.SendCommand` and `send` own the
single legacy/rich send transaction; `group_send` and `message_service` preserve
supported imports and legacy conflict adaptation. Edit/delete/read/forward keep
their existing current-authorized domain services and immutable receipt rules.
`event_names` defines committed message events and the moderation whitelist.

`MessagePage` prepares authorized history/context/lookup/starred/replay/search
relations and eligible rosters for one response. `ConversationPage` batches current direct inbox grants, people, restrictions,
blocks, latest visible messages, preferences and presence when moderation is off;
moderation-enabled/non-direct/legacy preparation keeps its existing current
boundaries. `ConversationRead` reuses the prepared facts across inbox fields. These objects
never authorize a later request, mutation, byte read, transcript or socket send.
Private attachment access lives in `services.attachment_access`; its view import
remains compatible. WebSocket middleware still guards both receive and send.

Legacy full lists remain compatible. Message pages accept `edits_page` and
`edits_page_size` (default 5, maximum 20) and expose `edit_history_page`; omitted
controls keep complete edit history. Forward destinations accept `bounded=true`
and their signed `cursor`, with 20 accepted rows and at most 100 candidates per
request. Empty result pages can still have `has_more=true`; follow the cursor.
Support GET retains its existing `bounded=true` relation pages. Support reply and
creation/reply recovery accept `receipt=compact`; full is the default. Retain
that reply choice with the original Idempotency-Key: changing the representation
on the same command conflicts. Compact recovery reports current ticket identity,
revision and status; paged detail supplies history.

PostgreSQL read receipts use one INSERT/SELECT with original synchronous read
timestamps and conflict protection; SQLite retains 500-object batches. This
bounds Python memory, not the database's work independently of unread count.
Presence remains connection-scoped and renewable; digest delivery chooses any
currently authorized source and rechecks each device at dispatch.

Run `make test-sprint09-communication CYCLE_SETTINGS=<isolated_settings>
BASELINE_OUT=<scratch_directory>` and `make sprint09-coverage`. Sprint 09 has
remaining acceptance limits, including compatible unbounded modes and moderated/group inbox
query work; see `sprints/evidence/sprint-09/README.md`.
