# ── Sukoon Monorepo Root Makefile ─────────────────────────
SHELL := /bin/bash

.DEFAULT_GOAL := help

# ── Help ────────────────────────────────────────────────
help:
	@echo "=========================================================="
	@echo "            Sukoon Platform Monorepo Commands             "
	@echo "=========================================================="
	@echo "Fullstack:"
	@echo "  make dev                   - Run backend & frontend dev servers"
	@echo ""
	@echo "Backend (Django / DRF / Channels):"
	@echo "  make backend-run           - Run backend server (uvicorn/port 8000)"
	@echo "  make backend-test          - Run backend pytest suite"
	@echo "  make backend-migrate       - Apply database migrations"
	@echo "  make backend-makemigrations- Create new database migrations"
	@echo "  make backend-shell         - Open Django shell_plus"
	@echo "  make backend-clean         - Remove backend cache & build files"
	@echo ""
	@echo "Frontend (Next.js / TypeScript):"
	@echo "  make frontend-install      - Install frontend dependencies"
	@echo "  make frontend-dev          - Start Next.js dev server (port 3000)"
	@echo "  make frontend-build        - Build Next.js production bundle"
	@echo "  make frontend-lint         - Run ESLint on frontend code"
	@echo ""
	@echo "Mobile (Flutter / Melos Monorepo):"
	@echo "  make mobile-analyze        - Melos analyze across all packages"
	@echo "  make mobile-test           - Run Flutter test suite across all packages"
	@echo "  make mobile-codegen        - Run build_runner code generation"
	@echo "  make mobile-translations   - Regenerate translation strings from lang.json"
	@echo "  make mobile-clean          - Clean Flutter/Melos build caches"
	@echo "=========================================================="

# ── Fullstack ───────────────────────────────────────────
dev:
	cd backend && pipenv run python scripts/dev.py

# ── Backend ─────────────────────────────────────────────
backend-run:
	cd backend && make run

backend-test:
	cd backend && make test

backend-migrate:
	cd backend && make migrate

backend-makemigrations:
	cd backend && make makemigrations

backend-shell:
	cd backend && make shell

backend-clean:
	cd backend && make clean

# ── Frontend ────────────────────────────────────────────
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

# ── Mobile ──────────────────────────────────────────────
mobile-analyze:
	cd mobile && melos exec -- dart analyze .

mobile-test:
	cd mobile && melos exec -- flutter test

mobile-codegen:
	cd mobile && melos exec -- dart run build_runner build -d

mobile-translations:
	cd mobile && dart run generate/strings/main.dart

mobile-clean:
	cd mobile && melos exec -- flutter clean

.PHONY: help dev backend-run backend-test backend-migrate backend-makemigrations backend-shell backend-clean frontend-install frontend-dev frontend-build frontend-lint mobile-analyze mobile-test mobile-codegen mobile-translations mobile-clean
