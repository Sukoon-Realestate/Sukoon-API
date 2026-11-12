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
