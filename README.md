# Sukoon Monorepo 🏢

Welcome to the **Sukoon** monorepo. Sukoon is a modern real estate platform comprising backend API services, an administrative web frontend, and cross-platform mobile applications.

---

## 📁 Repository Structure

```text
Sukoon-API/
├── backend/                  # Django 5.0 REST API & Channels Backend
│   ├── config/               # Settings split (local, sqlite, production, test)
│   ├── core_apps/            # Modular Django apps (users, properties, chat, etc.)
│   ├── manage.py             # Django management entry point
│   ├── Pipfile / Pipfile.lock# Python virtual environment & dependencies
│   ├── CLAUDE.md             # Backend AI agent instructions & conventions
│   └── .claude/              # Backend-specific Claude agents & skills
│
├── frontend/                 # Next.js 15 Web Application & Admin Portal
│   ├── src/app/              # Next.js App Router (dashboard, users, properties, etc.)
│   ├── package.json          # Node.js dependencies
│   ├── CLAUDE.md             # Frontend AI agent instructions
│   └── AGENTS.md             # Next.js specific agent rules
│
├── mobile/                   # Flutter 3.9+ & Melos Monorepo
│   ├── apps/
│   │   ├── sokoun_app/       # Main mobile app (tenant & owner experience)
│   │   └── landing_page/     # Mobile landing page application
│   ├── packages/
│   │   └── core/             # Shared kernel, networking, caching, and UI widgets
│   ├── pubspec.yaml          # Root Melos workspace configuration
│   ├── CLAUDE.md             # Mobile AI agent instructions & conventions
│   └── .claude/              # Mobile-specific Claude agents & skills
│
├── docs/                     # Cross-platform API handoffs & architecture guides
├── Makefile                  # Root monorepo developer commands
├── CLAUDE.md                 # Monorepo root AI orchestrator
└── README.md                 # Monorepo overview (this file)
```

---

## 🚀 Quick Start

Run `make help` to inspect all available commands across services.

### 1. Backend (`backend/`)
```bash
cd backend
pipenv install
pipenv run python manage.py migrate
pipenv run uvicorn config.asgi:application --reload --port 8000
```
*Alternatively, from repo root:* `make backend-run` or `make backend-test`.

### 2. Frontend (`frontend/`)
```bash
cd frontend
npm install
npm run dev
```
*Alternatively, from repo root:* `make frontend-dev`.

### 3. Mobile (`mobile/`)
```bash
cd mobile
melos bootstrap
melos exec -- flutter test
```
*Alternatively, from repo root:* `make mobile-analyze` or `make mobile-test`.

---

## 🤖 AI Assistant Conventions

- Monorepo orchestration: [CLAUDE.md](CLAUDE.md)
- Backend agent guides: [backend/CLAUDE.md](backend/CLAUDE.md)
- Frontend agent guides: [frontend/CLAUDE.md](frontend/CLAUDE.md)
- Mobile agent guides: [mobile/CLAUDE.md](mobile/CLAUDE.md)
