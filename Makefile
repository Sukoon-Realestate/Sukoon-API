PIPENV ?= pipenv

test:
	$(PIPENV) run pytest

test-cov:
	$(PIPENV) run pytest --cov=core_apps --cov-report=term-missing

dev:
	$(PIPENV) run python scripts/dev.py

dev-seed:
	$(PIPENV) run python scripts/dev.py --seed

dev-reset:
	$(PIPENV) run python scripts/dev.py --reset

seed:
	$(PIPENV) run python manage.py seed_db --settings=config.settings.local_sqlite

run:
	$(PIPENV) run uvicorn config.asgi:application --reload --host 127.0.0.1 --port 8000

makemigrations:
	$(PIPENV) run python manage.py makemigrations

migrate:
	$(PIPENV) run python manage.py migrate

collectstatic:
	$(PIPENV) run python manage.py collectstatic --no-input --clear

build:
	$(PIPENV) install && $(PIPENV) run python manage.py collectstatic --no-input

superuser:
	$(PIPENV) run python manage.py createsuperuser

shell:
	$(PIPENV) run python manage.py shell_plus

django_shell:
	$(PIPENV) run python manage.py shell_plus

lint:
	$(PIPENV) run flake8 .

lint-check:
	$(PIPENV) run black --check .

generate_token:
	python -c "import secrets; print(secrets.token_urlsafe(38))"
