# Project Rules

## Code Quality
- Write clean, readable, maintainable code
- Use clear, descriptive variable and function names
- Avoid overly complex logic — prefer simplicity
- Keep functions small and focused (single responsibility)
- Avoid magic values — use constants
- Follow consistent formatting (Black)

## Comments (Better Comments Convention)
Use comment prefixes consistently so intent is scannable at a glance:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `# *`  | Highlight — important note or section marker | `# * Access token settings` |
| `# ?`  | Explanation — why this exists or how it works | `# ? Lax prevents CSRF while allowing top-level nav` |
| `# !`  | Warning / side effect / critical info | `# ! Modifies the response object directly` |
| `# TODO` | Work remaining | `# TODO refactor into service layer` |

- Never write comments that just restate the code (`# loop through users`)
- Block comments explaining a setting or decision use `# ?`
- Side-effect warnings use `# !`

## API Architecture
- Use Django REST Framework
- Use `Response` with proper HTTP status codes
- Always version URLs: `/api/v1/<app>/`
- Use `django-filter` when more than one filter is needed
- Separate list, detail, create, update into distinct view classes — never combine unrelated actions in one class
- List endpoints must always be paginated (use the default `PageNumberPagination`)

## Project Structure
```
<app>/models/         # one file per model or logical domain
<app>/serializers/    # one file per domain
<app>/views/          # one file per domain
<app>/services/       # business logic, one file per domain
<app>/filters.py      # django-filter FilterSet classes
<app>/permissions.py  # custom DRF permission classes
<app>/signals.py      # signal handlers (connected in apps.py)
<app>/urls.py
<app>/tests/          # test_models.py, test_views.py, test_serializers.py, test_services.py
```

## Conventions
- Use `ModelSerializer`
- Follow existing project patterns exactly
- Use `select_related` / `prefetch_related` to optimize querysets
- Default auth: JWT (cookie-based via `CookieAuthentication`), `IsAuthenticated`

## Model Conventions
- Always inherit from `TimeStampedModel` (provides `pkid`, `id`, `created_at`, `updated_at`)
- Every model must define `__str__` returning a human-readable identifier
- Always define `class Meta` with at least `verbose_name`, `verbose_name_plural`, and `ordering`
- Use `UUID` for public-facing IDs (`id`), `BigAutoField` for internal PKs (`pkid`) — follow existing User/Profile pattern
- Never use `null=True` on string fields (`CharField`, `TextField`) — use `blank=True` with empty string default instead

## Serializer Conventions
- Use `read_only_fields` in `Meta` for fields that must never be written (e.g. `id`, `created_at`)
- Prefer `PrimaryKeyRelatedField` over nested serializers for write operations; use nested serializers for read-only representations
- `SerializerMethodField` is acceptable for computed/derived values — name the method `get_<field>`
- Use `validate_<field>` for single-field validation, `validate` for cross-field validation
- Never put business logic inside serializer `create`/`update` — delegate to a service

## URL & Naming Conventions
- URL names: `<domain>-list`, `<domain>-detail`, `<domain>-create`, `<domain>-update`, `<domain>-delete`
- View class names: `<Domain>ListAPIView`, `<Domain>DetailAPIView`, `<Domain>CreateAPIView`, `<Domain>UpdateAPIView`
- Serializer names: `<Domain>Serializer`, `<Domain>CreateSerializer`, `<Domain>UpdateSerializer` when shapes differ
- Filter class names: `<Domain>Filter` in `<app>/filters.py`
- Permission class names: `Is<Role>` or `Can<Action>` in `<app>/permissions.py`

## Permissions
- Default: `IsAuthenticated` — never leave a view with no permission class
- Write custom permissions in `<app>/permissions.py` as `BasePermission` subclasses
- Object-level permissions go in `has_object_permission` — always call `self.check_object_permissions(request, obj)` in the view before returning the object
- Ownership check pattern: `return obj.user == request.user`

## Signals
- Signals are acceptable ONLY for decoupled side effects: auto-creating related objects (e.g. Profile on User creation), invalidating caches
- Never put business logic or multi-step transactions in signals — put them in services
- Keep signal handlers in `<app>/signals.py` and connect them in `<app>/apps.py` via `ready()`

## Error Handling
- Services raise `rest_framework.exceptions.ValidationError` for business rule violations — DRF converts these to `400` automatically
- Services raise `rest_framework.exceptions.PermissionDenied` for authorization failures → `403`
- Services raise `django.core.exceptions.ObjectDoesNotExist` (or `Model.DoesNotExist`) for missing resources — views convert these to `404` via `get_object_or_404` or explicit `try/except`
- Never raise raw `Exception` or `ValueError` from services — always use typed exceptions
- Views do not need `try/except` for `ValidationError` — DRF handles it; only catch `DoesNotExist`

## Logging
- Every view file must define: `logger = logging.getLogger(__name__)`
- Log errors with `logger.error(...)`, unexpected states with `logger.warning(...)`
- Never log sensitive data (passwords, tokens, personal data)
- Do not log normal request flow — only log errors and unexpected branches

## Documentation
- Write docstrings for views, helper functions, and non-trivial logic
- For POST/PUT/PATCH: include `request.body` example in docstring
- For filters: document parameter keys and example values

## Database Performance (MANDATORY)
- Prevent N+1 queries — analyze queryset relations before writing queries
- `select_related` → ForeignKey / OneToOne
- `prefetch_related` → ManyToMany / reverse relations
- Never query inside loops
- Never serialize unoptimized querysets
- Do not access related fields in serializers without prior queryset optimization

## Testing
- **Tests are mandatory whenever a new feature is created** — include happy path, error cases, and edge cases
- Tests live in `<app>/tests/` package
- One file per concern: `test_models.py`, `test_views.py`, `test_serializers.py`, `test_services.py`
- Use pytest + pytest-django
- Use `APIClient.force_authenticate()` for authenticated view tests — never set JWT cookies manually
- When a bug is found, write a failing test before fixing it
- Coverage floor: 70% (enforced in CI via `--cov-fail-under=70`)
- Test services independently — no `APIClient`, just call the function directly with `@pytest.mark.django_db`
- For views using `select_related`/`prefetch_related`, add a query-count assertion using `django.test.utils.CaptureQueriesContext`
- Every endpoint must have: unauthenticated → 401, happy path, invalid payload → 400, not found → 404

## Strict Exclusions
- NEVER run `makemigrations` or `migrate`
- No templates
- No Django forms (except admin)
- No unrelated features or abstractions

## Performance Mode
- Prefer minimal diffs over full rewrites
- Modify only necessary lines/functions
- Assume existing code is correct unless stated otherwise
- Minimize token usage: no unnecessary context, no over-generation

## Service Layer

Place business logic in a `services/` package inside the app, not in views or serializers.

### Structure
```
<app>/services/
    <domain>_service.py
    __init__.py
```

### Rules
- Services handle business logic only — no request/response handling, no serializers, no HTTP logic
- Views stay thin: validate input via serializer, call service, return response
- Use `@transaction.atomic` for multi-step operations
- Name functions with clear action verbs: `create_order`, `cancel_order`, `complete_order`
- Serializer validates input format/types; service validates business rules
- DB performance rules apply inside services (no queries in loops, use select_related/prefetch_related)
- Handle external integrations (email, payments) inside services, not views

### Responsibilities
- **Serializer** → input validation (format, types)
- **Service** → business validation + execution
- **View** → orchestration only (call serializer → call service → return Response)

### Anti-Patterns (NEVER do these)
- Business logic inside views
- Calling serializers inside services
- Using `request` inside services

### Testing Services
- Test services independently with `@pytest.mark.django_db` — no APIClient needed
- Add `test_services.py` to `<app>/tests/`

### When to Use
Use a service when logic involves multiple models, transactions, non-trivial business rules, or needs reuse across views.
