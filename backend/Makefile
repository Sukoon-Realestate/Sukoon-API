# ── Sukoon Backend Makefile ──────────────────────────────
PYTHON ?= python
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
