# Backend Postman collection

Generated from local `main` at `3a289624213c59d547f4944b9d34c20ab53a04f8`.
The sprint checkout's application code was not used to generate these requests.

## Import and authenticate

1. Import `Sukoon_Backend_main.postman_collection.json` and, optionally,
   `Sukoon_Backend_local.postman_environment.json` into Postman.
2. Set `base_url` to your backend origin, without a trailing slash or `/api/v1`.
   The default is `http://127.0.0.1:8000`.
3. Set collection variables `email` and `password` to an existing account's
   credentials. Run **MVP available → api/auth/login → POST login**.
   Successful login, refresh and email verification scripts capture access and
   refresh tokens from the response envelope or response cookies. Protected
   requests inherit bearer authentication from `access_token`.
4. For registration, run the register request, set `otp` from the received email,
   then run a verification request. Replace the other example registration values.
5. Set the resource variables used in the selected request URL to real IDs.
   UUIDs and integer IDs are placeholders; they do not refer to seeded records.

Tokens are written to **collection variables**. Avoid creating environment
variables named `access_token` or `refresh_token`, which would shadow them.
Keep Postman's cookie jar enabled for cookie-based refresh. Switching account
or server may require clearing existing authentication cookies first.
Credentials and tokens are intentionally blank in the supplied files.

## Coverage and request templates

The collection includes **977 unique route/method requests**, including health:
445 allowed by the default MVP route policy and 532 deferred. Folders separate
these groups, then group requests by API family. Public routes override inherited
authentication. Other permissions, role checks, workspace restrictions and
feature configuration still apply to routes in the available folder.

The deferred folder requires server-side `SUKOON_MVP=false`; changing Postman
variables cannot enable these workflows. Additional service/provider switches
may also be required. The collection includes explicit aliases but omits 12
duplicate DRF format variants and one shadowed URL pattern. Native Django admin,
HTML/viewer/static routes and WebSocket messages are outside its scope.

Bodies use required writable serializer fields or declared Swagger parameters
where available. Optional declared query fields are supplied disabled. Uploads
use multipart form fields or binary file bodies; select your own files.
Serializer examples require valid values and the appropriate application state.
Some fields depend on a discriminator or runtime context; check the handler.

**400 mutation requests have no inspectable body declaration** and carry an
explicit note with their handler location. Their `{}` body is a starting template,
not a claim that no fields are required. Complete those command bodies from the
named handler/service before sending. The backend's full Swagger export currently
fails; individual inspection also fails for two requests. `coverage.json` records
the export counts and source revision.

Mutation requests include disabled `Idempotency-Key` and `If-Match` headers.
Enable these only where the command requires them, and supply an operation key
or current ETag. Keep a key for an identical retry; use a new key for a new command.
Provider callbacks and upload grants need their own signatures/credentials as
specified by the handler. Account authentication does not replace those grants.

This is a request catalog for selecting individual requests, not an ordered
end-to-end Collection Runner scenario. No requests were sent to a live backend
during generation or validation.

## Regenerate

From the repository root, using an existing checkout of the desired revision:

```sh
backend/.venv/bin/python backend/tools/export_postman.py \
  --backend-root /path/to/main-worktree/backend \
  --output backend/docs/postman
```

Without `--backend-root`, the exporter uses its own backend checkout. It records
that checkout's branch and exact commit in the output. Generation uses build
settings with a dummy database, disables dotenv loading, and makes no HTTP calls.
