test:
	pipenv run pytest

test-cov:
	pipenv run pytest --cov=core_apps --cov-report=term-missing

run:
	pipenv run uvicorn config.asgi:application --reload --host 127.0.0.1 --port 8000

makemigrations:
	pipenv run python manage.py makemigrations

migrate:
	pipenv run python manage.py migrate

collectstatic:
	pipenv run python manage.py collectstatic --no-input --clear

build:
	pipenv install && pipenv run python manage.py collectstatic --no-input

superuser:
	pipenv run python manage.py createsuperuser

shell:
	pipenv run python manage.py shell_plus

django_shell:
	pipenv run python manage.py shell_plus

lint:
	pipenv run flake8 .

lint-check:
	pipenv run black --check .

generate_token:
	python -c "import secrets; print(secrets.token_urlsafe(38))"
