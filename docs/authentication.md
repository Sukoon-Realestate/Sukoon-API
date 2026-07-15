# Authentication & Authorization Flow

Darak uses cookie-based JWT authentication combined with DRF permissions.

## Authentication Mechanism

1. **Login & Token Issuance**:
   - The user posts credentials to `/api/v1/auth/jwt/create/`.
   - The server validates the credentials and returns standard JWT tokens in the response body.
   - For web clients, authentication is configured via cookies using `CookieAuthentication`.

2. **JWT Configuration (`config/settings/base.py`)**:
   - **Access Token Lifetime**: 1 day
   - **Refresh Token Lifetime**: 2 days
   - **Rotate Refresh Tokens**: Enabled
   - **Auth Cookie Name**: `access`

## Authorization & Permissions

- Every API view MUST specify a `permission_classes` attribute.
- The default fallback is `IsAuthenticated`.
- Custom permissions can be written in `<app>/permissions.py` subclassing `BasePermission`.
