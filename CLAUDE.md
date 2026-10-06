# CLAUDE.md — Sukoon Monorepo Orchestrator

Sukoon is a multi-platform real estate ecosystem organized as a clean monorepo with three core workspaces:
1. `backend/`: Django REST API + Django Channels (WebSockets) + PostgreSQL/SQLite + SimpleJWT.
2. `frontend/`: Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS (Admin & Web Dashboard).
3. `mobile/`: Flutter 3.9+ + Dart + Melos 8 monorepo (`packages/core`, `apps/sokoun_app`, `apps/landing_page`).

---

## 🧭 Monorepo Routing Rule

**Always inspect the relevant workspace before making changes:**

| Target Workspace | Scope | Primary Configuration | Agent / Skill Location |
|---|---|---|---|
| **Backend** (`backend/`) | Django API, models, migrations, endpoints, serializers, Celery, Channels, auth | [backend/CLAUDE.md](file:///Users/demo23home/code/Sukoon-API/backend/CLAUDE.md) | `backend/.claude/agents/`, `backend/.claude/skills/` |
| **Frontend** (`frontend/`) | Next.js admin & portal, pages, React components, Tailwind styling, web client | [frontend/CLAUDE.md](file:///Users/demo23home/code/Sukoon-API/frontend/CLAUDE.md) | `frontend/AGENTS.md` |
| **Mobile** (`mobile/`) | Flutter tenant & owner apps, Melos packages, Clean Architecture, Cubits, UI widgets | [mobile/CLAUDE.md](file:///Users/demo23home/code/Sukoon-API/mobile/CLAUDE.md) | `mobile/.claude/agents/`, `mobile/.claude/skills/` |
| **Cross-Platform / Docs** (`docs/`) | API handoffs, Postman collections, architecture specifications | Root `docs/` | Cross-discipline |

---

## 🛠️ Root Commands (from Repo Root)

```bash
# ── Help ───────────────────────────────────────────
make help                     # Show all monorepo commands

# ── Backend Shortcuts ──────────────────────────────
make backend-run              # Start Django API dev server
make backend-test             # Run Django pytest suite
make backend-migrate          # Apply database migrations
make backend-makemigrations   # Create new database migrations
make backend-shell            # Open Django shell_plus

# ── Frontend Shortcuts ─────────────────────────────
make frontend-dev             # Start Next.js development server
make frontend-build           # Build Next.js production bundle
make frontend-lint            # Run ESLint on frontend

# ── Mobile Shortcuts ───────────────────────────────
make mobile-analyze           # Run Melos analyze across all packages & apps
make mobile-test              # Run Flutter tests across all packages & apps
make mobile-codegen           # Run build_runner code generation
make mobile-translations      # Generate localization strings from lang.json
make mobile-clean             # Clean Melos packages

# ── Fullstack Dev Runner ───────────────────────────
make dev                      # Start unified backend + frontend runner
```

---

## 🏗️ Architecture & Conventions by Workspace

### 1. Backend (`backend/`)
- Settings located in `backend/config/settings/` (`local_sqlite.py`, `local.py`, `production.py`, `test.py`).
- Apps located in `backend/core_apps/` (`users`, `profiles`, `properties`, `chat`, `notifications`, `support`, etc.).
- Function-based or service-backed API views with DRF serializers.
- JWT authentication (`SimpleJWT`) and role-based permissions (`Tenant`, `Owner`, `Admin`).

### 2. Frontend (`frontend/`)
- Next.js 15 App Router (`src/app/`) with TypeScript and Tailwind CSS.
- Authentication context with token refresh (`src/context/AuthContext.tsx`).
- API client abstraction in `src/lib/api/`.

### 3. Mobile (`mobile/`)
- Melos workspace managing `packages/core`, `apps/sokoun_app`, and `apps/landing_page`.
- Clean Architecture: Presentation (thin screens, extracted widgets, `AsyncCubit<T>`), Data (models, datasources), Domain (use cases).
- Navigation MUST use `Go` static helper (`Go.to`, `Go.back`, etc.) — never raw `Navigator`.
- Paginated lists MUST use `AppPagify`.
- Localization uses `LocaleKeys` sourced from `packages/core/assets/translations/lang.json`.

---

## 📝 ALWAYS — Log Completed Tasks to WORKLOG.md

After finishing **any task requested by the user**, append an entry to `WORKLOG.md` under today's date heading (`## YYYY-MM-DD`):
```markdown
### <short task title>
- **What:** <one line on what was done>
- **Why:** <reason / ticket context>
- **Details:** <key changes, decisions, anything the tech lead should notice>
- **Files:** <files touched>
```
