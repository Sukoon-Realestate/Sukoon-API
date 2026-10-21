# Phone capture development workbench

This is an implemented capture/upload/coaching development slice, not a completed
360 plus navigable 3D product. `releaseReady` remains false. CPU spherical
projection produces private, masked review artifacts. The worker is connected to
the isolated COLMAP/gsplat adapter and calls it only after the pinned CUDA runtime
probe succeeds. This workstation has no configured runtime, so 3D jobs remain in a
reason-coded needs-processing state. Owner review can fetch generated private
panorama and reconstruction thumbnails. Gaussian PLY rendering, validated
navigation, spherical hotspots and publication integration remain unfinished.

## Configuration already installed locally

- Settings module: `config.settings.capture_dev`.
- Database: dedicated PostgreSQL 16.15 cluster on `127.0.0.1:55435`, database
  `capture_dev`, private data in `backend/.capture-dev-postgres/` (ignored by Git).
  TCP and local connections use SCRAM authentication. The generated password is
  stored only in `.envs/property-capture-postgres-password` (0600, ignored).
- API: `http://127.0.0.1:8026/api/v1/` (loopback only).
- Private original/artifact directory: `backend/private_virtual_tours/capture-dev`.
- Secret: `GEMINI_API_KEY` in `backend/.envs/.env.local`, permission 0600,
  ignored by Git; never copy it into a Flutter define, asset, JavaScript or log.
- Model: `GEMINI_COACH_MODEL=gemini-3.8-live`.
- Limits: 512 MiB/session, 30 MiB/original, 1 MiB/upload part, 40 rooms,
  5,000 manifest frames, 120 frames/station for the initial CPU worker.
- Coaching: one active connection per account, 10 issued sessions per rolling
  day, 180 seconds/session, one credential use, 60 seconds to connect, selected
  JPEG at most every two seconds, longest edge 768. Provider audio is discarded.
- Jobs: 90-second renewable lease, at most three claims, 900-second worker budget.
  Cancel/ownership/deletion/lease checks fence final writes. Outputs are independent.
- Retention: inactive captures tombstoned after 30 days. Existing private-blob
  cleanup retains live references and removes unreferenced blobs after its
  seven-day grace period. Schedule `core_apps.virtual_tours.tasks.cleanup_tours` through
  the existing Celery task runner. Deletion immediately revokes API access; physical
  deletion is asynchronous. No automatic local-device deletion is added yet.

`capture.env.example` contains the nonsecret environment contract. Main production
settings default `PROPERTY_CAPTURE_ENABLED=false`. The local settings module turns
on the development path. No running remote server has been deployed or reconfigured.

## Reproduce setup

From `Sukoon-API/backend`:

```bash
.venv/bin/python -m pip install -r tools/virtual_tours/capture-requirements.txt
bash tools/virtual_tours/run_capture_dev.sh
# In another terminal while the workbench runs:
.venv/bin/python manage.py check_property_capture_config --settings=config.settings.capture_dev --probe-gemini --strict
```

The combined script requires `initdb` and `pg_ctl` on PATH. It creates or reuses
only its dedicated database cluster, migrates and seeds it, then starts the API
and worker. It refuses an unrelated occupied port and stops its owned processes
on exit, including PostgreSQL if it started that cluster. A cluster that was
already running is retained. Existing development/production databases are not used.
If the workbench is already running, keep those processes. Independent commands,
when deliberately managing the database separately, are:

```bash
.venv/bin/python tools/virtual_tours/capture_dev_postgres.py start
.venv/bin/python manage.py migrate --settings=config.settings.capture_dev
.venv/bin/python manage.py prepare_property_capture_demo --settings=config.settings.capture_dev
.venv/bin/python manage.py runserver 127.0.0.1:8026 --settings=config.settings.capture_dev --noreload
.venv/bin/python manage.py run_property_capture_worker --settings=config.settings.capture_dev
```

`--once` processes at most one queued job. SQLite is not used for the running
capture workbench: a real HTTP test exposed writer contention with the polling
worker. The initial local fixture was migrated to the dedicated PostgreSQL cluster,
preserving the property/user IDs. The old `capture-dev.sqlite3` and protected
`.envs/property-capture-sqlite-export.json` are retained as local backups.
For a deployment, use PostgreSQL and shared private storage. The preflight checks
configuration, migrations, storage write/fsync and optional model access. It does
not fabricate a GPU or a real-capture pass.

## Private demonstration listing

- Title: `عقار اختبار الجولة الافتراضية`
- ID: `3b5462c9-2b14-4b8f-8b7e-3a25e750fe93`
- Status: hidden, without synthetic media presented as a property result.
- Local fixture: `.envs/property-capture-demo.json` (0600, ignored).
- Login email: `capture-demo@sokoun.test`; password exists only in that local file.
- The command reuses the listing and refreshes the local token. It refuses any
  settings module other than `capture_dev`. Its account verification is a local
  QA fixture, not evidence of a real person's identity verification.

## Android preparation

From `darak-app/apps/sokoun_app`:

```bash
/Users/aait/Downloads/flutter_3.44_7/bin/flutter pub get
/Users/aait/Downloads/flutter_3.44_7/bin/flutter build apk --debug --flavor dev --target-platform android-arm64 --no-pub --dart-define=SOKOUN_CAPTURE_API_BASE_URL=http://127.0.0.1:8026/api/v1/
```

The override is honored only in debug builds with the `dev` flavor. It writes the
existing development base URL store, and does not modify Firebase Remote Config.
Only loopback HTTP or HTTPS endpoints are accepted. The debug-only Android network
policy allows cleartext for localhost/127.0.0.1; release networking is unchanged.

For the later physical capture, connect the supported device and run:

```bash
/Users/aait/Library/Android/sdk/platform-tools/adb reverse tcp:8026 tcp:8026
/Users/aait/Downloads/flutter_3.44_7/bin/flutter run --flavor dev --dart-define=SOKOUN_CAPTURE_API_BASE_URL=http://127.0.0.1:8026/api/v1/
```

Sign in to the local QA account, select Owner, edit the demonstration property,
then choose the camera/capture action. Existing prepared-tour management also has
`Capture with phone`. A new property must be saved before its capture session can
be associated with its server identity. Grant camera permission and confirm the
room capture consent. Gemini is a separate opt-in. A valid supported-device
check remains necessary even when Google Play Services for AR is installed.

## iOS preparation

```bash
cd darak-app/apps/sokoun_app/ios
pod install --no-repo-update
```

ARKit, AVFoundation, CoreImage and CryptoKit are system frameworks. Deployment
target is iOS 15. Camera usage text already exists in the app. The local plugin is
registered in generated plugin registration and Podfile.lock. The pod was built
for arm64/iphoneos without code signing; this is not a signed application or device
capture test. For a real iPhone, supply a reachable HTTPS development API using
`SOKOUN_CAPTURE_API_BASE_URL`, configure normal signing, connect/trust the device
and enable Developer Mode. `127.0.0.1` on an iPhone is not this Mac; no fake localhost
route, unsigned deployment, or second camera session is assumed.

## API and schemas

All routes below are under `/api/v1/`, require authentication and return the normal
`message`/`data` envelope. Capture owner, current property owner and non-retired
property must match. Responses are private/no-store. Mutations except binary
parts and ephemeral credential provisioning require the existing `Idempotency-Key`
contract. Request identity survives ambiguous outcomes in the protected Flutter
operation journal.

| Method/path | Purpose |
| --- | --- |
| GET `properties/capture-capabilities/` | Enabled flag, policy and explicit `releaseReady: false` |
| GET/POST `properties/{property}/capture-sessions/` | List/create; stable client UUID deduplicates |
| GET/PATCH/DELETE `property-captures/{session}/` | Status, active/pause/consent, tombstone |
| POST `property-captures/{session}/rooms/` | Scoped room UUID, label and owner confirmation |
| POST `property-captures/{session}/coach-sessions/` | Nonpersisted, constrained short-lived credential |
| POST `property-captures/{session}/uploads/` | Reserve immutable frame ID, bytes, hash, metadata |
| GET `.../uploads/{asset}/` | Durable received part indexes |
| PUT `.../uploads/{asset}/parts/{one-based-index}/` | Exact-sized binary part, identical replay allowed |
| POST `.../uploads/{asset}/complete/` | Verify all parts, SHA256, JPEG, dimensions and orientation |
| POST `.../manifests/` | Expected revision plus immutable, scoped verified inputs |
| POST `.../processing-jobs/` | Deduplicate by immutable revision and server profile |
| GET/POST `.../processing-jobs/{job}/` | Status / cancellation |
| GET `.../processing-jobs/{job}/stations/{station}/{image-or-mask}/` | Authenticated private result bytes |
| GET `.../processing-jobs/{job}/components/{component}/{thumbnail-or-preview-or-detail-or-cameras-or-navigation}/` | Authenticated private reconstruction artifact |

Set `CAPTURE_RECONSTRUCTION_ENABLED=true`,
`CAPTURE_RECONSTRUCTION_PYTHON=/absolute/path/to/pinned/python`, and
`CAPTURE_RECONSTRUCTION_COLMAP=/absolute/path/to/colmap` only in the isolated
worker environment after installing the exact PyTorch 2.7.1 CUDA,
pycolmap 3.12.6 CUDA, gsplat 1.5.3 runtime. The worker performs a version/CUDA
probe before processing and strips backend/provider credentials from its child
process. A passing probe is runtime readiness only, not room reconstruction,
navigation or quality validation.

Structural input schemas are in `property-capture.schema.json`. Authoritative
cross-field, finite-matrix, scoped-identity and real-byte checks are in
`capture_validation.py` and `capture_services.py`. Matrices are row-major
`T_world_camera_optical`; world is right-handed Y-up, optical image axes right/down/
forward. Timestamps are decimal strings. Depth is explicitly null in this RGB
profile. AR resets create new coordinate components, never an identity alignment.

## Tests

```bash
# Django/DRF database and processing regressions
.venv/bin/python -m pytest core_apps/virtual_tours/tests --disable-warnings

# Real PostgreSQL row-locking/concurrency coverage, in a temporary owned cluster.
# Requires initdb, pg_ctl and createdb on PATH; refuses an occupied test port.
bash tools/virtual_tours/test_capture_postgres.sh

# From darak-app/apps/sokoun_app, with the workbench API and worker running
CAPTURE_QA_FIXTURE_PATH=/Users/aait/Desktop/StudioProjects/Sukoon-API/backend/.envs/property-capture-demo.json CAPTURE_QA_GEMINI=1 /Users/aait/Downloads/flutter_3.44_7/bin/flutter test --no-pub test/property_capture_http_integration_test.dart

/Users/aait/Downloads/flutter_3.44_7/bin/flutter test --no-pub test/property_capture_test.dart test/property_capture_recovery_test.dart test/virtual_tours_test.dart test/tour_editor_recovery_test.dart test/owner_tour_manager_test.dart
```

The HTTP test performs real cookie login through production `DioService`, starts a
private session, uploads the first 1 MiB, pauses/resumes through `CaptureApi`, verifies
real JPEG bytes, finalizes/deduplicates a job, waits for the actual polling worker,
checks partial/failed independent outputs, optionally opens a real Gemini Live
connection, then cancels and tombstones the synthetic test session. It never claims
a random-noise protocol fixture is a room. Credentials are read from the ignored
fixture; they are never embedded in the test or app. Omit `CAPTURE_QA_GEMINI` for a
provider-free run. No microphone/audio/real-room provider test has run.

`test_capture_postgres.sh` creates a new cluster on loopback port 55436, uses
`config.settings.postgres_test` with explicit test credentials, and stops only its
own cluster on exit. It leaves its private temporary directory and logs for
inspection. Override the test port with `CAPTURE_TEST_PG_PORT` when needed.
`run_capture_dev.sh` supervises both its API and worker; if either stops, the other
is shut down. A strict preflight with `--probe-gemini` fails when the requested
model cannot be reached or does not report Live support. Local configuration
readiness is separate from the always-false release gate in this development slice.

## Troubleshooting and remaining gates

- Disabled path: inspect capture-capabilities and the settings module; do not bypass
  the flag or publish gate. Prepared-media tour capabilities are a different contract.
- Permission/service failure: grant camera permission, check ARCore support/install,
  or use an ARKit-capable iPhone. Resume starts a new tracking component.
- Provider failure/quota/expiry: local capture and guidance continue; close coaching
  and reconnect explicitly after the one-active-session budget expires.
- `ASSET_NOT_VERIFIED`: read received parts, resume exact missing bytes, retain the
  original ID/hash. Never replace an ambiguous request with a fresh identity.
- `needsCapture`: capture the missing real views. Masked holes are not filled by AI.
- `PROCESSING_CAPACITY_UNAVAILABLE` for 3D: the reconstruction pipeline is not wired.
  Implement/refine COLMAP + pinned gsplat training, component alignment, geometry
  validation, mobile viewer, and independent readiness checks on the actual GPU.
- Crash/lease expiry: the polling worker retries within three claims. A superseded
  lease cannot commit. Inspect the immutable job/revision instead of republishing.
- Out of disk: stop only owned work and remove confirmed-unused generated caches.
  Preserve source, live Gradle caches, original captures and QA evidence.
- Next real-device gate: Android RGB and iPhone RGB/no-depth datasets; moving people,
  glare, textureless walls, full zenith/nadir, station drift, tracking reset,
  occlusion, interruption, restart, measured RAM/thermal/FPS and weak-network tests.
- Full-sphere seam quality/exposure correction, owner-confirmed hotspots, 3D
  continuous positional navigation and verified mode-switch transforms remain open.
- A model/GPU cost per room cannot be measured before real capture/reconstruction.
  Only bounded configuration and local synthetic runtimes are available now.
