# ── Configuration ───────────────────────────────────────
# Python interpreter (override with: make run PYTHON=python3.12)
PYTHON ?= python

.DEFAULT_GOAL := help

# ── Help ────────────────────────────────────────────────
help:
	@echo "Available commands:"
	@echo "  install          - Install Python dependencies"
	@echo "  run              - Run the development server"
	@echo "  migrate          - Apply database migrations"
	@echo "  migrations       - Create new migrations"
	@echo "  shell            - Open the Django shell"
	@echo "  test             - Run the test suite"
	@echo "  superuser        - Create a superuser"
	@echo "  static           - Collect static files"
	@echo "  check            - Run Django system checks"
	@echo "  clean            - Remove __pycache__ and *.pyc files"
	@echo "  clean-migrations - Delete migration files (keeps __init__.py)"

# ── Django ──────────────────────────────────────────────
install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) manage.py runserver

mi:
	$(PYTHON) manage.py migrate

make:
	$(PYTHON) manage.py makemigrations

shell:
	$(PYTHON) manage.py shell

test:
	$(PYTHON) manage.py test

superuser:
	$(PYTHON) manage.py createsuperuser

static:
	$(PYTHON) manage.py collectstatic --noinput

check:
	$(PYTHON) manage.py check

# ── Utilities ───────────────────────────────────────────
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

clean-migrations:
	find apps -path "*/migrations/*.py" ! -name "__init__.py" -delete
	find apps -path "*/migrations/*.pyc" -delete

.PHONY: help install run migrate migrations shell test superuser static check clean clean-migrations
