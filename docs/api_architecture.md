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

### 3. Property discovery and visits

- `GET /api/v1/properties/governorates/`: paginated governorate list.
- `GET /api/v1/properties/cities/?governorate=<uuid>`: paginated cities,
  optionally filtered by governorate. Governorates and cities are managed in
  Django admin.
- `GET /api/v1/properties/available_places/?property_type_id=<uuid>`: distinct
  approved-property locations for a property type.
- `GET /api/v1/properties/<property_id>/`: property details, including the
  `amenities`, `is_fav`, `is_saved`, and aggregate `rating` fields.
- `GET /api/v1/properties/<property_id>/available_dates/?date=YYYY-MM-DD`:
  future availability configured by that property's owner. If `date` is
  omitted, `times` describes the first date in `days`.
- `POST /api/v1/properties/<property_id>/visits/`: book an owner slot; the slot
  is checked again transactionally when the request is created.

Availability expiry and all past/future comparisons use the configured
`Africa/Cairo` timezone. Machine-readable booking values use `YYYY-MM-DD` dates
and `HH:mm:ss` times.

---

## Response Formatting
Every response from the API uses JSON formatting and proper HTTP status codes.

For detailed development rules, please refer back to [CLAUDE.md](file:///home/demo/code/Darak/Darak-API/CLAUDE.md).
