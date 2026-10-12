# ── Sukoon Backend Makefile ──────────────────────────────
PYTHON ?= python
CYCLE_PYTHON ?= .venv/bin/python
CYCLE_SETTINGS ?= config.settings.postgres_test
CYCLE_EVIDENCE ?= ../docs/qa/owner-tenant-source-verification
PIPENV ?= pipenv
ROOT_ENV_FILE ?= ../.env
REMOTE_SETTINGS ?= config.settings.production

.DEFAULT_GOAL := help

# ── Help ────────────────────────────────────────────────
help:
	@echo "Sukoon Backend - Available commands:"
	@echo "  install          - Install dependencies using pipenv"
	@echo "  run              - Run the development server (uvicorn/runserver)"
	@echo "  migrate          - Apply database migrations"
	@echo "  makemigrations   - Create new migrations"
	@echo "  shell            - Open Django shell_plus / shell"
	@echo "  test             - Run pytest test suite"
	@echo "  test-cov         - Run pytest with coverage"
	@echo "  superuser        - Create a superuser"
	@echo "  static           - Collect static files"
	@echo "  check            - Run Django system checks"
	@echo "  seed             - Seed SQLite database with test data"
	@echo "  clean            - Remove __pycache__ and *.pyc files"

# ── Setup & Run ─────────────────────────────────────────
install:
	$(PIPENV) install

run:
	$(PIPENV) run uvicorn config.asgi:application --reload --host 127.0.0.1 --port 8000

run-manage:
	$(PIPENV) run python manage.py runserver

migrate:
	$(PIPENV) run dotenv -f $(ROOT_ENV_FILE) run -- $(PYTHON) manage.py migrate --settings=$(REMOTE_SETTINGS)

makemigrations:
	$(PIPENV) run python manage.py makemigrations

shell:
	$(PIPENV) run python manage.py shell_plus

# ── Testing & Quality ───────────────────────────────────
test:
	$(PIPENV) run pytest

test-cov:
	$(PIPENV) run pytest --cov=core_apps --cov-report=term-missing

.PHONY: test-owner-tenant test-visit-booking test-cycle-contract check-owner-tenant
test-owner-tenant: ## Run rental, property, advertising and renderer regressions on an isolated DB
	$(CYCLE_PYTHON) -m pytest core_apps/features/tests core_apps/advertising/tests core_apps/properties/tests core_apps/common --ds=$(CYCLE_SETTINGS) --junitxml=$(CYCLE_EVIDENCE)/owner-tenant.xml

test-visit-booking: ## Verify visit booking, owner schedules and group visit integration
	$(CYCLE_PYTHON) -m pytest core_apps/properties/tests core_apps/features/tests/test_planning_cycles.py --ds=$(CYCLE_SETTINGS) --junitxml=$(CYCLE_EVIDENCE)/visit-booking.xml

test-cycle-contract: ## Generate fresh Django API responses for the Flutter contract test
	SOKOUN_CONTRACT_ARTIFACT_DIR=$(abspath $(CYCLE_EVIDENCE)) $(CYCLE_PYTHON) -m pytest core_apps/features/tests/test_rental_phase2.py::test_phase2_complete_interest_to_activation_flow --ds=$(CYCLE_SETTINGS)

check-owner-tenant: ## Check Django configuration and migration source consistency
	$(CYCLE_PYTHON) manage.py check --settings=$(CYCLE_SETTINGS)
	$(CYCLE_PYTHON) manage.py makemigrations --check --dry-run --settings=$(CYCLE_SETTINGS)

check:
	$(PIPENV) run python manage.py check

lint:
	$(PIPENV) run flake8 .

# ── Management ──────────────────────────────────────────
superuser:
	$(PIPENV) run python manage.py createsuperuser

static:
	$(PIPENV) run python manage.py collectstatic --noinput

seed:
	$(PIPENV) run python manage.py seed_db --settings=config.settings.local_sqlite

# ── Utilities ───────────────────────────────────────────
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .pytest_cache .coverage

.PHONY: help install run run-manage migrate makemigrations shell test test-cov check lint superuser static seed clean

.PHONY: test-remaining-cycles test-flutter-request-bodies
test-remaining-cycles: ## Exercise remaining cycles and export real planning/refund API contracts
	SOKOUN_PLANNING_ARTIFACT_DIR=$(abspath $(CYCLE_EVIDENCE)) SOKOUN_CONTRACT_ARTIFACT_DIR=$(abspath $(CYCLE_EVIDENCE)) $(CYCLE_PYTHON) -m pytest core_apps/features/tests/test_planning_cycles.py core_apps/features/tests/test_planning_boundaries.py core_apps/features/tests/test_funded_settlement.py core_apps/features/tests/test_remaining_concurrency.py core_apps/features/tests/test_full_cycle_http.py --ds=$(CYCLE_SETTINGS) --junitxml=$(CYCLE_EVIDENCE)/remaining-cycles.xml

test-flutter-request-bodies: ## Feed the actual Flutter-serialized request bodies back into Django
	SOKOUN_FLUTTER_REQUEST_BODIES=$(abspath $(CYCLE_EVIDENCE))/flutter-request-bodies.json $(CYCLE_PYTHON) -m pytest core_apps/features/tests/test_flutter_request_roundtrip.py --ds=$(CYCLE_SETTINGS) --junitxml=$(CYCLE_EVIDENCE)/flutter-request-roundtrip.xml
