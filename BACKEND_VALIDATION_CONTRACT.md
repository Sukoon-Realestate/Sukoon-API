# Backend Field Validation Contract

Updated: 2026-10-02  
Contract Version: `v1.0.0`  
Application: Sukoon Real Estate API (`/api/v1/`)

---

## Global Overview & Conventions

1. **Authentication:** 
   - Public endpoints require no authentication credentials.
   - Protected endpoints accept cookie-based JWT authentication (`access` HTTP-only cookie) or standard `Authorization: Bearer <access_token>` header.
2. **Standard Response Envelopes:**
   - **Success (GET):** `{"data": { ... }}`
   - **Success (POST / PUT / PATCH / DELETE):** `{"message": "...", "data": { ... }}`
   - **Validation Error (HTTP 400):** `{"message": "Field Name: <specific error message> ..."}`
   - **Authentication Error (HTTP 401):** `{"message": "Given token not valid for any token type"}` or `{"message": "Authentication credentials were not provided."}`
   - **Permission Denied (HTTP 403):** `{"message": "You do not have permission to perform this action."}`
   - **Not Found (HTTP 404):** `{"message": "Not found."}`
   - **Rate Limiting (HTTP 429):** `{"message": "Request was throttled. Expected available in <seconds> seconds."}`
3. **Character Encoding:** All text fields are UTF-8 compliant.
4. **General Phone Format:** Accepts local Egyptian mobile format (e.g. `01012345678`), national formatted strings, or international standard E.164 format (`+201012345678`).

---

## POST /api/v1/auth/users/

*Note: `POST /api/v1/auth/register/` is a direct alias for this flow.*  
**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `first_name` | String | Yes | Rejected (400) | 1–50 Unicode characters | Unicode letters, combining marks, spaces, hyphens, apostrophes | Trim surrounding whitespace | None | `required`, `blank`, `max_length` |
| `last_name` | String | Yes | Rejected (400) | 1–50 Unicode characters | Unicode letters, combining marks, spaces, hyphens, apostrophes | Trim surrounding whitespace | None | `required`, `blank`, `max_length` |
| `email` | String | Yes | Rejected (400) | Max 254 characters | Standard RFC 5322 email syntax (`local <= 64`, `domain <= 254`) | Trim and convert to lowercase | Must be unique across all accounts | `required`, `invalid`, `unique` |
| `phone_number` | String | No | Allowed (blank default) | 11 digits (Egyptian) / E.164 | `^01[0125][0-9]{8}$` or `+201[0125][0-9]{8}` | Parsed & formatted by PhoneNumberField | Stored in user profile | `invalid` |
| `birth_date` | String | No | Allowed (null) | Date format | `YYYY-MM-DD` | None | Stored in user profile | `invalid` |
| `password` | String | Yes | Rejected (400) | Min 8 characters | Non-empty, non-whitespace | Exact value preserved | Validated via Django password validators | `required`, `min_length`, `password_too_common` |
| `re_password` | String | Yes | Rejected (400) | Min 8 characters | Same as `password` | Exact value preserved | Must match `password` identically | `password_mismatch` |

- **Valid request example:**
```json
{
  "first_name": "Ahmed",
  "last_name": "Ali",
  "email": "ahmed.ali@example.com",
  "phone_number": "01012345678",
  "password": "StrongPassword123!",
  "re_password": "StrongPassword123!"
}
```

- **Invalid request examples and complete responses:**
  - Duplicate Email:
    ```json
    {
      "message": "Email: user with this Email already exists."
    }
    ```
  - Password Mismatch:
    ```json
    {
      "message": "Non Field Errors: The two password fields didn't match."
    }
    ```
  - Invalid Egyptian Phone:
    ```json
    {
      "message": "Phone Number: The phone number entered is not valid."
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `201 Created` — Registration successful, verification OTP dispatched via email.
  - `400 Bad Request` — Validation failure (duplicate email, mismatch password, invalid phone).
  - `429 Too Many Requests` — Registration throttling exceeded.

- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A (JSON endpoint).
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** Triggers initial 6-digit OTP with 10-minute expiration.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** None. Backend validates names, trimmed lowercase email, Egyptian phone numbers, and non-whitespace passwords.
- **Rules the mobile app must add or revise:** Mobile may continue sending local `01xxxxxxxxx` numbers; backend normalizes into profile storage.

---

## POST /api/v1/auth/login/

*Note: `POST /api/v1/auth/jwt/create/` is also supported.*  
**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `email` | String | Yes | Rejected (400) | Max 254 chars | Valid email | Trimmed, case-insensitive match | Must match registered user | `required`, `invalid` |
| `password` | String | Yes | Rejected (400) | Min 1 char | Exact string | None | Checked against user password hash | `required`, `invalid_credentials` |

- **Valid request example:**
```json
{
  "email": "ahmed.ali@example.com",
  "password": "StrongPassword123!"
}
```

- **Invalid request examples and complete responses:**
  - Invalid credentials:
    ```json
    {
      "message": "Detail: No active account found with the given credentials"
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — Successful authentication. Returns tokens in body and sets HTTP-only `access` and `refresh` cookies.
  - `400 Bad Request` — Missing email or password.
  - `401 Unauthorized` — Wrong email or password.
  - `429 Too Many Requests` — Rate limit exceeded.

- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** Standard brute-force throttling rules apply.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** None.
- **Rules the mobile app must add or revise:** None.

---

## POST /api/v1/auth/verify/

*Note: `POST /api/v1/auth/verify-email/` and `POST /api/v1/auth/verify-otp/` are direct aliases.*  
**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `email` | String | Yes | Rejected (400) | Max 254 chars | Valid email | Trimmed & lowercased | Must match registered user | `required`, `invalid` |
| `otp` | String | Yes | Rejected (400) | Exactly 6 ASCII digits | `^[0-9]{6}$` | Trimmed | Verified against active cached OTP | `required`, `max_length`, `min_length`, `invalid` |

- **Valid request example:**
```json
{
  "email": "ahmed.ali@example.com",
  "otp": "482910"
}
```

- **Invalid request examples and complete responses:**
  - Expired or invalid code:
    ```json
    {
      "message": "Otp: The verification code has expired or is invalid. Please request a new one."
    }
    ```
  - Wrong OTP code:
    ```json
    {
      "message": "Otp: Invalid verification code."
    }
    ```
  - Max attempts exceeded (5 failed attempts):
    ```json
    {
      "message": "Otp: Too many failed attempts. Please request a new verification code."
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — Email verified. Returns user payload and sets authentication cookies.
  - `400 Bad Request` — Invalid or expired OTP code.
- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** 10 minutes OTP lifetime, max 5 failed attempts before lockout.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** None.
- **Rules the mobile app must add or revise:** None.

---

## POST /api/v1/auth/resend-otp/

**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `email` | String | Yes | Rejected (400) | Max 254 chars | Valid email | Trimmed & lowercased | Account must exist and not already be verified | `required`, `invalid` |

- **Valid request example:**
```json
{
  "email": "ahmed.ali@example.com"
}
```

- **Invalid request examples and complete responses:**
  - Cooldown active (within 60s):
    ```json
    {
      "message": "Detail: Please wait before requesting another verification code."
    }
    ```
  - Already verified:
    ```json
    {
      "message": "Email: This email is already verified."
    }
    ```
  - Account does not exist:
    ```json
    {
      "message": "Email: User with this email does not exist."
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — New OTP generated and dispatched via email.
  - `400 Bad Request` — Cooldown active, email already verified, or email not found.
- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** 60-second cooldown enforced on server cache. OTP valid for 10 minutes.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** Confirms 60-second cooldown and 10-minute code expiry.
- **Rules the mobile app must add or revise:** Mobile 60s countdown timer matches server cooldown.

---

## POST /api/v1/auth/users/reset_password/

**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `email` | String | Yes | Rejected (400) | Max 254 chars | Valid email | Trimmed & lowercased | If account exists, sends reset link | `required`, `invalid` |

- **Valid request example:**
```json
{
  "email": "ahmed.ali@example.com"
}
```

- **Invalid request examples and complete responses:**
  - Invalid email syntax:
    ```json
    {
      "message": "Email: Enter a valid email address."
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `204 No Content` — Password reset email dispatched (silent success prevents email enumeration).
  - `400 Bad Request` — Malformed email syntax.
- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** Reset token expires in 24 hours.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** Returns HTTP 204 No Content.
- **Rules the mobile app must add or revise:** Handle HTTP 204 as successful request confirmation.

---

## POST /api/v1/auth/google/

**Authentication:** None (Public)  
**Content-Type:** `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `token` | String | Yes | Rejected (400) | Non-empty | Valid Google OAuth2 ID token | Trimmed | Verified against Google OAuth2 tokeninfo | `required`, `blank`, `invalid` |

- **Valid request example:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1NiIs..."
}
```

- **Invalid request examples and complete responses:**
  - Invalid/expired Google ID token:
    ```json
    {
      "message": "Detail: Invalid Google token."
    }
    ```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — Authenticated successfully. User created/linked and JWT cookies returned.
  - `400 Bad Request` — Invalid or expired Google token.
- **Upload limits (bytes, MIME, dimensions), if applicable:** N/A.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** N/A.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** None.
- **Rules the mobile app must add or revise:** None.

---

## PATCH /api/v1/profiles/edit/

*Note: `PATCH /api/v1/profiles/user/update/` is also supported.*  
**Authentication:** Required (`IsAuthenticated`)  
**Content-Type:** `multipart/form-data`, `application/json`, or `application/x-www-form-urlencoded`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `full_name` | String | No | Allowed | 1–100 chars | Unicode letters, spaces, hyphens, apostrophes | Trimmed; splits into `first_name` and `last_name` | None | `max_length` |
| `first_name` | String | No | Allowed | 1–50 chars | Unicode letters, spaces, hyphens, apostrophes | Trimmed | Updates User `first_name` | `max_length` |
| `last_name` | String | No | Allowed | 1–50 chars | Unicode letters, spaces, hyphens, apostrophes | Trimmed | Updates User `last_name` | `max_length` |
| `phone_number` | String | No | Allowed | 11 digits / E.164 | Egyptian mobile `^01[0125][0-9]{8}$` or `+20...` | Normalized by PhoneNumberField | Updates Profile `phone_number` | `invalid` |
| `gender` | String | No | Allowed | Enum (6 chars) | `"male"`, `"female"` | None | Updates Profile `gender` | `invalid_choice` |
| `birth_date` | String | No | Allowed (null) | Date | `YYYY-MM-DD` | None | Updates Profile `birth_date` | `invalid` |
| `avatar` | File / Data URI | No | Allowed (null/omitted) | Max 10 MB | JPEG, PNG, WEBP, GIF | Uploaded to Cloudinary storage | Also accepted via `profile_image` or `image` aliases | `invalid_image` |

- **Valid request example:**
```json
{
  "full_name": "محمد أحمد",
  "phone_number": "01012345432",
  "gender": "male",
  "birth_date": "1995-03-15"
}
```

- **Success response (HTTP 200 OK):**
```json
{
  "message": "Updated successfully.",
  "data": {
    "full_name": "محمد أحمد",
    "first_name": "محمد",
    "last_name": "أحمد",
    "email": "ahmed.ali@example.com",
    "phone_number": "+201012345432",
    "masked_phone_number": "010****432",
    "birth_date": "1995-03-15",
    "birth_date_label": "15 مارس 1995",
    "gender": "male",
    "gender_label": "ذكر",
    "avatar": "https://res.cloudinary.com/.../image.jpg",
    "profile_image": "https://res.cloudinary.com/.../image.jpg"
  }
}
```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — Profile updated.
  - `400 Bad Request` — Invalid phone number, gender choice, or corrupt image.
  - `401 Unauthorized` — Unauthenticated user.
- **Upload limits (bytes, MIME, dimensions), if applicable:** Max 10MB file size. Allowed image formats: JPEG, PNG, WEBP, GIF.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** N/A.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** Accepts `avatar`, `profile_image`, or `image` interchangeably for image uploads.
- **Rules the mobile app must add or revise:** Mobile may send `full_name` or `first_name`/`last_name`.

---

## POST /api/v1/auth/complete-register/

**Authentication:** Required (`IsAuthenticated`)  
**Content-Type:** `multipart/form-data` or `application/json`  
**Contract version / effective date:** `v1.0.0` / 2026-10-02

| Field | JSON/form type | Required condition | Blank/null/omitted | Min/max and unit | Allowed values or format | Normalization | Uniqueness/cross-field rules | Error code |
|---|---|---|---|---|---|---|---|---|
| `national_id` | String | No | Allowed (omitted if unchanged) | Exactly 14 digits | `^[0-9]{14}$` (ASCII digits only) | Trimmed | Stored in user profile | `max_length`, `min_length`, `invalid` |
| `front_id_image` | File / Data URI | No | Allowed (omitted if unchanged) | Max 10 MB | JPEG, PNG, WEBP | Uploaded to Cloudinary (`profile_documents/id_face/`) | Preserved if omitted | `invalid_image` |
| `back_id_image` | File / Data URI | No | Allowed (omitted if unchanged) | Max 10 MB | JPEG, PNG, WEBP | Uploaded to Cloudinary (`profile_documents/id_back/`) | Preserved if omitted | `invalid_image` |
| `selfie_image` | File / Data URI | No | Allowed (omitted if unchanged) | Max 10 MB | JPEG, PNG, WEBP | Uploaded to Cloudinary (`profile_documents/selfie/`) | Preserved if omitted | `invalid_image` |

- **Valid request example (Multipart Form Data):**
  - `national_id`: `"29503151234567"`
  - `front_id_image`: `<binary image file>`
  - `back_id_image`: `<binary image file>`
  - `selfie_image`: `<binary image file>`

- **Success response (HTTP 200 OK):**
```json
{
  "message": "Operation successful.",
  "data": {
    "registration_complete": true,
    "verification_status": "pending",
    "missing_fields": []
  }
}
```

- **Success and validation/authentication/throttling HTTP statuses:**
  - `200 OK` — KYC documents submitted/updated.
  - `400 Bad Request` — Invalid national ID length or corrupt image files.
  - `401 Unauthorized` — Unauthenticated user.
- **Upload limits (bytes, MIME, dimensions), if applicable:** Max 10MB per document image. Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`.
- **Cooldown/expiry/attempt limit and retry metadata, if applicable:** N/A.
- **Differences from BACKEND_FIELD_VALIDATIONS.md:** Allows partial submission for existing accounts; previously uploaded documents are preserved.
- **Rules the mobile app must add or revise:** Mobile can continue using partial updates and check `missing_fields` and `registration_complete` flags in the response.
