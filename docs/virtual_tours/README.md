# Virtual tours: API, worker and storage runbook

Date: 2026-10-15. Source: `backend/core_apps/virtual_tours`.

The owner/tenant workflow, file requirements, examples and limits are documented in [the cross-repository implementation guide](../../../darak-app/SOKOUN_VIRTUAL_TOURS_IMPLEMENTATION.md). This runbook describes how to configure and operate the implementation. Configuration snippets are instructions; they were not applied to a live deployment.

## 1. Components and data ownership

| Component | Responsibility |
|---|---|
| Django API | Owner authorization, inventory scope, upload receipts, revision ETags, review and session/resource access |
| PostgreSQL | Tour/revision/asset/variant/upload/operation/session/review records; transactional retries and competing edits |
| Celery worker | Decode panorama sources, build tiles, validate GLBs/collision/spawns and publish immutable prepared variants |
| Celery beat | Redispatch durable queued jobs every 60 seconds; reclaim interrupted jobs; hourly retention cleanup |
| Private storage | Completed sources, staging parts and scoped derivatives. Either a shared private volume or a private S3-compatible bucket |
| Static HTTPS viewer | Marzipano panoramas; Three.js/Rapier interiors; isolated read credential; no application JWT |
| Django admin | Per-revision, per-package inspection and hash-bound review with a required reason; emergency disable |

The migration is `backend/core_apps/virtual_tours/migrations/0001_initial.py`. It adds eight models: `PropertyVirtualTour`, `TourRevision`, `TourAsset`, `TourVariant`, `TourUploadSession`, `TourOperation`, `TourViewerSession`, and `TourReviewEvent`. External IDs are UUIDs; Django admin review URLs use the internal numeric primary key.

Source assets are immutable after upload completion. A clone receives new asset records referencing the immutable blobs, and the authoring IDs are remapped. Publication is one active revision pointer per property/kind. A rejected replacement does not replace that pointer.

## 2. Dependencies and configuration

Use the pinned Python 3.11 environment in `backend/Pipfile.lock` and the pinned Node dependencies in `backend/tools/virtual_tours/package-lock.json`. The API needs the Python dependencies; the processing worker also needs a supported Node runtime and the Node validation tools.

```sh
cd backend
pipenv sync
cd tools/virtual_tours
npm ci
```

Configure these values on both the API and worker where applicable. Values below are examples, not credentials or a live host:

```dotenv
VIRTUAL_TOUR_PRIVATE_ROOT=/var/lib/sokoun/private-tours
VIRTUAL_TOUR_VIEWER_URL=https://api.example.com/tours/
VIRTUAL_TOUR_GLTF_VALIDATOR=/app/backend/tools/virtual_tours/validate-glb.cjs
VIRTUAL_TOUR_SPAWN_VALIDATOR=/app/backend/tools/virtual_tours/validate-spawns.mjs

VIRTUAL_TOUR_PANORAMA_READ=false
VIRTUAL_TOUR_PANORAMA_WRITE=false
VIRTUAL_TOUR_MODEL_READ=false
VIRTUAL_TOUR_MODEL_WRITE=false
```

The validator scripts are executable, use `/usr/bin/env node`, run without a shell, and have a bounded subprocess timeout. `node` must be on the worker's `PATH`. Model write capability fails closed when either validator path is absent. The source app also requires a valid HTTPS viewer URL with exact `/tours/` path and no username, password, query or fragment.

Existing broker, database and Celery settings remain the repository's normal settings. Do not copy production credentials into test settings. Flags default to false; migrations alone do not enable the feature.

### 2.1 Shared private filesystem

With `VIRTUAL_TOUR_S3_BUCKET` unset, API and worker processes must mount the **same durable private volume at the same path**. Directories use mode 0700 and files 0600. The volume must not be mounted under `MEDIA_URL`, static hosting, a public web root or a public CDN.

An ephemeral filesystem on separate API/worker instances is not a durable shared storage implementation. Use the object-storage option below for that topology.

### 2.2 Private S3 or DigitalOcean Spaces

```dotenv
VIRTUAL_TOUR_S3_BUCKET=sokoun-private-tours
VIRTUAL_TOUR_S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
VIRTUAL_TOUR_S3_REGION=us-east-1
VIRTUAL_TOUR_S3_PREFIX=sokoun-virtual-tours
VIRTUAL_TOUR_PRIVATE_ROOT=/tmp/sokoun-private-tour-cache
```

For AWS S3, leave `VIRTUAL_TOUR_S3_ENDPOINT` empty and set the actual bucket region. For Spaces, use the regional endpoint and the SDK configuration appropriate to that account. Credentials come from the normal AWS SDK environment/role chain; never put them in source control. See [DigitalOcean's SDK configuration](https://docs.digitalocean.com/products/spaces/reference/aws-sdks/) and [Boto3 object upload](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html).

Use a dedicated **private** bucket/prefix with public access and CDN delivery disabled. Grant the API/worker only the required object get/put/list/delete permissions in that prefix. Enable provider encryption and backups/versioning according to deployment policy. The application does not provision a bucket or change its public-access policy.

The gateway streams parts into bounded private local files, persists them to the bucket, and then records acceptance. Completion reads staged parts, verifies the complete hash, and writes a **different** opaque completed-asset key. Workers persist tiles before a variant can become ready. A different API instance can materialize an authorized source/tile from the bucket into its private cache. Provider URLs are never returned to tenants: every delivered byte still passes the current database policy checks.

Keys are server-generated UUIDs. Clients cannot choose or overwrite a completed object key. Retrying a signed staging URL cannot change the copied completed object. Configure a nonempty dedicated prefix containing letters, digits, underscores or hyphens. Cleanup only removes recognized opaque keys under this prefix and never sweeps another feature's bucket prefix.

Object storage does not require browser CORS here because only Django/worker processes contact it. The web shell and API use the same HTTPS origin. Provider integration has local protocol-fake coverage; real AWS/Spaces credentials, policies, replication and billing were not exercised.

## 3. Schema and viewer build

### Existing-service deployment (no additional subscription)

An existing Cloudinary account can also be the private backing store:

```dotenv
VIRTUAL_TOUR_STORAGE_PROVIDER=cloudinary
VIRTUAL_TOUR_CLOUDINARY_PREFIX=sokoun-virtual-tours
VIRTUAL_TOUR_PROCESSOR_MODE=inline
VIRTUAL_TOUR_PROCESSING_WIDTH=4096
VIRTUAL_TOUR_VIEWER_URL=https://your-existing-api.example/tours/
```

Reuse the service's existing Cloudinary SDK credentials; do not create a public
upload preset. Raw assets use `type=authenticated`. Large sources are split into
8 MiB objects with a size/SHA-256 manifest committed last, preserving the 30 MiB
panorama contract on a plan with a 10 MB raw-object limit. Tiles are private raw
objects. Provider URLs stay server-side; cache misses use 60-second signed API
downloads, bounded reads and atomic private files. Retention only sweeps the
dedicated prefix and excludes referenced source/variant/upload keys.

`inline` starts one daemon thread through ASGI lifespan, sharing the API process's
Django imports. A container file lock prevents simultaneous processors across
API workers, while database claims protect each job during rolling deployments.
It uses the same durable queued state and interrupted-job recovery as Celery.
This is a low-throughput option for an existing service: monitor API latency,
memory and backlog. It does not run unrelated scheduled tasks. Shutdown stops
polling; a forcibly interrupted job is reclaimed after 20 minutes. `polling` with
`python manage.py run_virtual_tour_worker` remains available for an existing
dedicated runtime. Defaults remain `celery` and S3/local storage.

4096 processing width reduces decoded memory while preserving the original
private source. Validate real memory under the deployed service's load before
increasing processing concurrency or width. It does not change accepted image
dimensions or the delivery schema. Monitor the existing provider's quota; this
configuration does not provision or upgrade any paid resource.

The API serves the checked-in viewer bundle from `backend/tour_viewer` at
`/tours/`, with a restricted CSP and same-origin admin embedding. Rebuild from
the Flutter repository with:

```sh
make -C apps/sokoun_app tourViewerApiBundle TOUR_API_OUTPUT=/path/to/Sukoon-API/backend/tour_viewer
```

Commit the generated bundle and its SHA-256 build manifest together. Before
restarting an ephemeral API container, preserve any *other* features' private
local files using their approved backup/restore procedure. Tour durability does
not make unrelated local storage durable.

Export contracts without touching deployment data:

```sh
cd backend
.venv/bin/python manage.py export_virtual_tour_contracts ../docs/virtual_tours/contracts --settings=config.settings.test
.venv/bin/python manage.py export_virtual_tour_contracts ../../darak-app/apps/virtual_tour_viewer/contracts --settings=config.settings.test
```

Exports include [OpenAPI](contracts/openapi.json), [authoring](contracts/authoring-v1.schema.json), [delivery](contracts/delivery-v1.schema.json), [walk regions](contracts/walk-regions-v1.schema.json), and [bridge commands](contracts/bridge-command-v1.schema.json). Keep both checkout copies synchronized when changing the source contracts. `npm run build` compiles the viewer's schema validators ahead of time, so contract validation does not need `eval` in production.

```sh
cd /path/to/darak-app/apps/virtual_tour_viewer
npm ci
npm run build
```

Serve `dist/` on the API/admin origin at exactly `/tours/`. See [the Nginx example](../../../darak-app/apps/virtual_tour_viewer/deploy/nginx.conf.example). The asset URL base is baked in as `/tours/`.

Required deployment properties:

- A valid trusted TLS certificate; no mixed content or certificate-error bypass.
- CSP limited to the app's own scripts/connect destinations and required WASM/blob image capabilities. No arbitrary frame, object, navigation or form targets.
- `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and disabled camera/microphone/geolocation permissions.
- `Cache-Control: private, no-store` on manifests, credentials, grants and private bytes. The static hashed application code can be cached separately.
- Do not log signed query strings, bootstrap tokens, `X-Tour-Credential` or owner JWTs. Disable/redact access logs on private delivery routes and redact equivalent fields in APM/error collectors.
- Allow raw PUT parts of 8 MiB plus transport overhead. The example allows 9 MiB at the proxy. Route raw parts to Django without converting them to multipart form fields.
- Check the existing API throttles and proxy connection limits using realistic tile volume. Do not silently remove throttling. Tune only after measuring legitimate concurrency and abuse limits.

The Flutter viewer trusts the configured API origin by default. If a dedicated viewer origin is required, build Flutter with `--dart-define=SOKOUN_TOUR_VIEWER_ORIGIN=https://viewer.example.com` and provide a same-origin API reverse proxy there. The staff popup preview currently requires viewer and admin to share the same HTTPS origin.

## 4. Release sequence

1. Provision private durable storage and least-privilege access. Back up the database and storage under the deployment's normal policy.
2. Deploy API/worker source and pinned dependencies with all four feature flags false.
3. Apply migrations through the normal release job using the intended deployment settings. Run Django checks and inspect the actual migrated database.
4. Deploy the static viewer and headers; collect Django static assets for the reviewer console. Confirm its exact trusted URL.
5. Start the normal Celery worker and beat services. Verify the worker can read/write private storage and execute both validator scripts.
6. Enable owner writes for the intended kind while keeping public reads false. Use an authorized non-production listing to prepare and privately preview real content.
7. Submit and inspect every scoped variant. Confirm source/date/origin, privacy, scale, collision, doors, return connections and allowed places before approval.
8. Run owner and tenant journeys on actual Android and iOS builds, including app termination, interrupted uploads, expired sessions, account switching and mid-session unpublish.
9. Enable public reads for the validated kind. Fetch fresh capabilities and availability from the actual deployed application, then open an authenticated/anonymous tenant session according to product access rules.

Useful deployment commands, executed only in the correct configured environment:

```sh
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
python manage.py virtual_tour_health
celery -A config worker --loglevel=INFO
celery -A config beat --loglevel=INFO
```

The repository's existing worker/service topology may wrap these commands. Do not create a duplicate beat scheduler. On a platform that reuses its current image on Restart, perform the platform's code rebuild/deploy action and verify the active release; a restart alone is not evidence of new source.

## 5. Review guide

Open Django admin → Tour revisions → **Inspect packages and review**. View permission is required for private preview; change permission is required for the decision. The preview dropdown lists the exact processed contexts. Approval requires the current source hash and a nonempty reason.

For every package:

1. Compare mapped room/bed/offer IDs with current rental inventory and confirm that the package can only expose those spaces plus permitted common areas.
2. Inspect the full panoramic view or every model area, including views through doors/windows/mirrors and objects that may contain documents, faces or device screens.
3. Inspect all connections/return paths or approved spawns. For interiors, verify realistic scale, ground, wall corners, closed doors and open doorways; hold movement against a wall and try diagonal approaches.
4. Confirm that a partial offer's actual downloaded package does not contain excluded rooms. Labels, hidden meshes and UI restrictions do not prove byte-level separation.
5. Record what was inspected and approve the exact hash or reject with a useful corrective reason. Owners revise rejected content by cloning it; they cannot mutate a reviewed revision in place.

Use Tour admin → **Disable viewing immediately** for an urgent privacy or content problem. New manifest/grant/byte requests fail after disable, including requests through an old session. Bytes already downloaded to an active process cannot be recalled from the device.

## 6. Processing, retention and monitoring

`process_tour` has a 900-second hard limit and 840-second soft limit. A queued revision is durable even if the broker is temporarily unavailable. Beat redispatches queued jobs; workers claim them transactionally. Interrupted processing older than 20 minutes can be reclaimed up to three times. Stale source hashes cannot replace current prepared output.

Hourly cleanup performs these operations:

| Data | Policy |
|---|---|
| Viewer sessions | Remove records more than one day beyond expiry |
| Successful operation receipts | Clear results after 30 days, retaining permanent key/hash tombstones |
| Open upload sessions | Mark expired after seven days |
| Abandoned mutable revisions | Delete after 30 days without updates when not processing or active |
| Unreferenced blobs/tiles/parts | Delete after seven days |
| Object-storage local cache | Old cache entries may be removed; authorized reads rematerialize from the bucket |
| Submitted/reviewed history | Retained while referenced; there is no automatic deletion of audit history |

Do not add a bucket lifecycle rule that deletes referenced approved sources or packages by age alone. Enablement requires a reviewed business retention policy for old immutable revisions and review history. The source quota is 2 GiB per revision, including recently opened/aborted upload reservations; staging parts and completed copies can temporarily add storage beyond the logical source size.

`python manage.py virtual_tour_health` emits aggregate revision states, queue age counters, logical source bytes, open upload count and active sessions. It emits no source paths, owner data or credentials. Feed it into the deployment's monitoring system and alert on:

- Queued work older than five minutes, repeated worker recovery or processing older than 20 minutes.
- Processing failures, missing assets, failed object-store writes/reads and increasing storage consumption.
- Bootstrap/renewal/resource authorization failures, unusual part traffic and unexpected rate-limit responses.
- Device-measured load time, interaction failures, memory growth and frame performance after release.

These counters and review records are implemented; a hosted monitoring dashboard and billing alerts still need deployment configuration. Logical source-byte counts include references/clones and are not a provider invoice or physical-byte measurement.

## 7. Rollback and recovery

For an incident, set the affected kind's read flag false first; set write false too if preparation is implicated. These switches are checked at actual asset access. Existing ordinary property media and rental actions remain independent.

Preserve the database, immutable assets, receipts and review history while investigating. Do not roll back the migration by dropping tables, replace persisted idempotency keys, expose the private bucket, or publish a broader package to hide a missing scoped variant. Redeploy compatible API/viewer versions and reopen a session after recovery. A revoked/expired bootstrap cannot be reused.

For a stuck upload, read its status and received parts. Resume with the same bytes and current part grants. A checksum mismatch requires correcting the file; accepted part bytes cannot be overwritten with different content. Expired/aborted sessions require a new explicit upload, while the old operation receipt is reconciled first.

For a draft conflict, obtain the current revision/ETag and retain the local edit for comparison. Submitted content requires a new revision. After a room/bed mapping change, prepare and review a new scope package instead of trying to bypass the stale fingerprint.

## 8. Local development and calibration

Generate labeled synthetic assets without writing to a property or database:

```sh
cd backend
.venv/bin/python tools/virtual_tours/generate_calibration.py /tmp/sokoun-tour-calibration
node tools/virtual_tours/validate-glb.cjs /tmp/sokoun-tour-calibration/visual.glb
```

The folder contains two labeled 4096×2048 panoramas, a simple interior GLB, collision GLB, walk regions, spawn configuration and an explicit synthetic-use notice. These fixtures are for calibration/automated development. They are not an authorized real property's tour and must not be represented as one.

Run focused checks with a task-owned PostgreSQL database (UTF-8), not the production `.env` database:

```sh
cd backend
TEST_POSTGRES_DB=sokoun_tour_test \
TEST_POSTGRES_USER=local_test_user \
TEST_POSTGRES_HOST=127.0.0.1 \
TEST_POSTGRES_PORT=55435 \
make test-virtual-tours
.venv/bin/python manage.py check --settings=config.settings.test
.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

SQLite can run most tests with `--ds=config.settings.test`, but the two concurrency tests intentionally require PostgreSQL. See [local verification](../../../darak-app/docs/verification/virtual_tours/LOCAL_VERIFICATION.md) for the exact completed checks and evidence boundaries.
