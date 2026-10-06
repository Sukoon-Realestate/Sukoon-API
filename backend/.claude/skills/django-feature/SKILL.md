---
name: django-feature
description: Build features in the GeenadeProject Django 5 + DRF codebase the right way. Use when adding a new app, model, DRF endpoint, serializer, filter, or JWT-protected view, or when running migrations/tests. Encodes this project's specific layout (Project/ settings package + settings_modules split, apps/ directory, Makefile shortcuts, SimpleJWT, django-filter, Unfold admin) and its function-based-view convention.
---

# GeenadeProject Django Feature Workflow

This project uses a `Project/` settings package with a focused `settings_modules/` split. Follow these conventions exactly — they differ from a vanilla `startproject`.

## Two rules that apply to ALL code you write here

1. **Views are function-based.** Every endpoint is a `@api_view`-decorated function. Do **not**
   add `APIView`, `ViewSet`, or DRF generic class views (`ListCreateAPIView`, etc.). The
   established pattern lives in `apps/access/views.py` — match it.
2. **Write the least code a human can read at a glance.** Prefer clarity and brevity over
   cleverness or boilerplate. No layers, helpers, or abstractions a feature doesn't need.
   A short, obvious function beats a "correct" but verbose class hierarchy. If a serializer or
   helper isn't pulling its weight, inline it.

## Project layout

```
Project/                  # settings PACKAGE + project plumbing (DJANGO_SETTINGS_MODULE = "Project.settings")
  env.py                  # django-environ; loads a SINGLE .env from the repo root
  settings.py             # main settings: INSTALLED_APPS, MIDDLEWARE, then `from Project.settings_modules import *`
  settings_modules/       # focused setting modules: drf, jwt_settings, cors, admin, db_config,
                          #   ckeditor5, email_sending, otp, sessions, logger, unfold_settings
  urls.py                 # ROOT_URLCONF — api_urls + third_party_urls lists
  cdn/                    # storage backends (conf.py imported last in settings.py)
  asgi.py / wsgi.py
apps/                     # ALL local Django apps live here
  access/                 # RBAC: decorators, permissions, checks, codes — reuse these
.env                      # secrets at repo ROOT (gitignored); ENVIRONMENT/DEBUG/DJANGO_SECRET_KEY/...
manage.py                 # sets DJANGO_SETTINGS_MODULE = "Project.settings"
Makefile                  # use these targets instead of raw manage.py
```

Settings module is `Project.settings`, NOT `config.django` or `config.settings`. Env values come
from one repo-root `.env`; `ENVIRONMENT` (`local` default | `test` | `Production`) is read from
inside that file. There is **no** `ENV/.env.<env>` directory and **no** `config/` package.

## Use the Makefile (don't call manage.py directly)

| Task | Command |
|------|---------|
| Run dev server | `make run` |
| Make migrations | `make make` |
| Apply migrations | `make mi` |
| Run tests | `make test` |
| Django system check | `make check` |
| Open shell | `make shell` |
| Create superuser | `make superuser` |
| Collect static | `make static` |
| Install deps | `make install` |

Override environment: `make test ENVIRONMENT=test` (default `local`). The virtualenv lives at
`./Venv/` — use `./Venv/bin/python` if you must call Python directly.

## Adding a new app

1. Create it under `apps/`:
   ```bash
   cd apps && ../Venv/bin/python ../manage.py startapp <app_name>
   ```
2. In `apps/<app_name>/apps.py`, `AppConfig.name` MUST be dotted from the repo root:
   ```python
   class <AppName>Config(AppConfig):
       default_auto_field = "django.db.models.BigAutoField"
       name = "apps.<app_name>"
   ```
3. Register it in `Project/settings.py` under the `LOCAL_APPS` section of `INSTALLED_APPS`:
   ```python
   # LOCAL_APPS
   "apps.<app_name>",
   ```
4. Wire URLs in `Project/urls.py` by appending to the `api_urls` list:
   ```python
   api_urls = [
       path("api/<app_name>/", include("apps.<app_name>.urls")),
   ]
   ```
5. `make make && make mi`.

## DRF conventions (configured in `Project/settings_modules/drf.py`)

- **JWT is the global default authenticator** (`DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]`).
  So a protected view only needs `@permission_classes([IsAuthenticated])` — you do **not** repeat
  `authentication_classes`. A **public** endpoint opts out with `@authentication_classes([])`.
- Pagination: `PageNumberPagination`, `PAGE_SIZE = 20` (applies to DRF generic/paginated responses;
  a plain `@api_view` returning a `Response(list)` is not auto-paginated — paginate manually only
  if a list is genuinely large).
- Filtering backend: `DjangoFilterBackend` (global default).
- Throttle rates: `user` 100/hour, `anon` 10/minute, `otp_request` 3/hour.

### Function-based view pattern (the only pattern to use)

```python
# apps/<app_name>/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.<app_name>.models import Thing


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def things(request):
    if request.method == "POST":
        thing = Thing.objects.create(name=request.data["name"])
        return Response({"id": thing.id, "name": thing.name}, status=201)
    qs = Thing.objects.all()
    return Response([{"id": t.id, "name": t.name} for t in qs])
```

```python
# apps/<app_name>/urls.py
from django.urls import path

from apps.<app_name> import views

app_name = "<app_name>"

urlpatterns = [
    path("things/", views.things, name="things"),
]
```

Reach for a `ModelSerializer` only when a payload is large or reused across endpoints; for a few
fields, an inline dict is shorter and clearer. Keep non-trivial business logic out of the view —
but don't add a `services.py`/`selectors.py` layer for a one-liner.

### RBAC (reuse `apps/access`, don't reinvent)

Role/permission/branch gating already exists as decorators. Stack them under `@api_view`:

```python
from apps.access.decorators import branch_required, permission_required, role_required
from apps.users.models import Role

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(Role.ADMIN, Role.AGENT)
def order_list(request):
    ...
```

`apps/access/checks.py` has query-scoping helpers (e.g. `visible_orders(user, qs)`) — use them to
scope querysets by role instead of re-deriving access rules per view.

### JWT / auth endpoints

Header is `Authorization: Bearer <token>`, `AccessToken`, HS256 (`Project/settings_modules/jwt_settings.py`).
Login/refresh: SimpleJWT's `TokenObtainPairView` / `TokenRefreshView` are already wired in
`apps/registration/urls.py` — reuse those rather than writing new token views.

## Admin (Unfold)

`unfold` is installed before `django.contrib.admin` (required). Register models in
`apps/<app_name>/admin.py` as usual; Unfold styles them. Admin is served at `/admin/`.

## Before finishing any change

1. `make check` — Django system checks pass.
2. `make make && make mi` — if models changed.
3. `make test` — tests pass.
4. Lint/format clean: flake8 (`flake8_django`, max line length **120**, `F401` ignored) and Black
   (line-length 120, see `pyproject.toml`). Migrations, `static`, and `manage.py` are excluded.

## Gotchas specific to this repo

- `DJANGO_SETTINGS_MODULE` is `Project.settings`. There is no `config/` package.
- Settings are split across `Project/settings_modules/*` and pulled in via
  `from Project.settings_modules import *` at the bottom of `Project/settings.py`.
- A missing repo-root `.env` raises `ImproperlyConfigured` at startup (`Project/env.py`).
- `SECRET_KEY` is `DJANGO_SECRET_KEY` from `.env`; never hardcode it.
- Local app paths are dotted as `apps.<name>` everywhere (INSTALLED_APPS, AppConfig.name, includes).
- `AUTH_USER_MODEL = "users.User"`. Health check endpoint already exists at `/health/`.
