# API Architecture & Endpoints

This document describes the general architecture of the Darak API.

## Versioning
All endpoints are versioned and follow the prefix `/api/v1/`.

## Core Endpoints

### 1. Authentication
Endpoints are powered by `djoser` and custom extensions in `core_apps.users`.

- `POST /api/v1/auth/users/`: Register a new user.
- `POST /api/v1/auth/jwt/create/`: Log in and receive access/refresh tokens.
- `POST /api/v1/auth/jwt/refresh/`: Refresh token.
- `GET /api/v1/auth/users/me/`: Retrieve current user details.

### 2. User Profiles
Endpoints for viewing and updating user profiles:

- `GET /api/v1/profiles/me/`: Retrieve current user's profile.
- `PATCH /api/v1/profiles/me/update/`: Update profile details.
- `GET /api/v1/profiles/all/`: Retrieve all profiles (paginated).

---

## Response Formatting
Every response from the API uses JSON formatting and proper HTTP status codes.

For detailed development rules, please refer back to [CLAUDE.md](file:///home/demo/code/Darak/Darak-API/CLAUDE.md).
