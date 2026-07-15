# Darak API

Darak is a premium real estate platform API built with Django and Django REST Framework.

## Features

- **User Authentication & Management**: Secure authentication via JWT cookies utilizing Djoser and Django REST Framework.
- **User Profiles**: Profiles linked directly with user records containing gender, birth date, etc.
- **Content View Tracking**: Generic, unique tracking of page/content views by user and viewer IP address.
- **Interactive Documentation**: Beautiful API documentation using ReDoc and Swagger/OpenAPI specifications.
- **Quality & Testing**: Configured with `pytest` and `pytest-django` for automated test suites.

---

## Documentation Index

Detailed documentation for the project structure, API design, and rules:

1. [Coding Rules & Project Conventions (CLAUDE.md)](CLAUDE.md)
2. [API Architecture & Endpoints](docs/api_architecture.md)
3. [Database & Models Design](docs/database_models.md)
4. [Authentication & Authorization Flow](docs/authentication.md)

---

## Development Setup

### Prerequisites

- Python 3.11+
- Pipenv
- PostgreSQL database

### Installation & Run

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd Darak-API
   ```
2. Install dependencies:
   ```bash
   pipenv install --dev
   ```
3. Set up your environment variables in `.envs/.env.local`.
4. Run migrations:
   ```bash
   make migrate
   ```
5. Start the development server:
   ```bash
   make run
   ```
   The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### API Docs

Access the ReDoc interactive documentation at:
[http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)
