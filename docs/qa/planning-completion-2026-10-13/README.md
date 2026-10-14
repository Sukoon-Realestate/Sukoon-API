# Seven planning features — local verification, 2026-10-13

Implemented in `Sukoon-API/backend` and the companion `/Users/aait/Desktop/StudioProjects/darak-app/apps/sokoun_app` checkout. The API repository's `mobile/` directory was not synchronized. No push, deployment or live provider operation was performed.

## Final results

| Check | Result |
|---|---|
| PostgreSQL features/properties/notifications/profiles/common regressions | 621 passed, 0 failed/errors/skipped; includes 8 actual Flutter request-body roundtrips |
| Enabled Flutter planning target | 81 passed, 5 disabled-build cases skipped |
| Explicit disabled Flutter build | All 5 opposite-mode cases passed; private requests suppressed |
| Flutter renewal/lifecycle/recovery regressions | 55 passed |
| Django response parsing and actual Flutter request export | 21 passed |
| Layout matrix, included in enabled planning | 360 cases across 10 surfaces, 6 widths, 3 text scales, Arabic/light and English/dark |
| Scoped Flutter analysis | No errors/warnings; one existing chat `TickerMode.of` info (analyzer exit code 1) |
| Django check and migration drift | Passed; no missing model changes; test migrations include features/0017 |
| Android dev debug, verification bypass false | APK built successfully |
| Whitespace checks | Both repositories passed |

Flutter groups overlap; do not add their counts as unique tests. The backend suite is scoped to the listed domains, not every application in the repository. Pytest emitted 482 warning records including dependency deprecations and fixture timezone warnings. Android reported future Gradle/AGP compatibility warnings.

`summary.json` records counts, boundaries and the final APK SHA-256. `postgres-junit.xml` retains testcase names/timings and suite counts, with captured output and host metadata removed. Result files retain final command summaries. No account tokens, Google keys or real customer payloads are included.

## Reproduction

SDK: Flutter 3.44.7 / Dart 3.12.2; backend Python 3.11 / Django 4.2.11. Use an isolated local PostgreSQL database. This run used port 55439, user `aait`, and database `sokoun_planning_local`; these are test-only settings.

From `backend`, export fresh Django fixtures first (the directory may be any local temporary directory):

```sh
SOKOUN_PLANNING_ARTIFACT_DIR=/tmp/sokoun-planning-contracts \
SOKOUN_CONTRACT_ARTIFACT_DIR=/tmp/sokoun-planning-contracts \
TEST_POSTGRES_DB=sokoun_planning_local TEST_POSTGRES_USER=aait TEST_POSTGRES_PORT=55439 \
.venv/bin/python -m pytest \
  core_apps/features/tests/test_planning_cycles.py \
  core_apps/features/tests/test_planning_boundaries.py \
  core_apps/features/tests/test_funded_settlement.py \
  core_apps/features/tests/test_rental_phase2.py \
  core_apps/features/tests/test_change_recovery.py \
  core_apps/features/tests/test_ongoing_cycle_http.py \
  --ds=config.settings.postgres_test -q
```

From the companion `apps/sokoun_app`, parse those responses and export real Flutter request bodies:

```sh
make test-django-remaining-contract \
  FLUTTER=/Users/aait/Downloads/flutter_3.44_7/bin/flutter \
  DJANGO_REMAINING=/tmp/sokoun-planning-contracts
make test-planning-cycles FLUTTER=/Users/aait/Downloads/flutter_3.44_7/bin/flutter
```

Then run the backend regressions with the exported bodies:

```sh
SOKOUN_FLUTTER_REQUEST_BODIES=/tmp/sokoun-planning-contracts/flutter-request-bodies.json \
SOKOUN_PLANNING_ARTIFACT_DIR=/tmp/sokoun-planning-contracts \
SOKOUN_CONTRACT_ARTIFACT_DIR=/tmp/sokoun-planning-contracts \
TEST_POSTGRES_DB=sokoun_planning_local TEST_POSTGRES_USER=aait TEST_POSTGRES_PORT=55439 \
.venv/bin/python -m pytest \
  core_apps/features/tests core_apps/properties/tests \
  core_apps/notifications/tests core_apps/profiles/tests core_apps/common \
  --ds=config.settings.postgres_test -q --junitxml=/tmp/sokoun-planning-regressions.xml
```

Additional final Flutter runs:

```sh
flutter test --no-pub test/planning_completion_contract_test.dart \
  test/rental_lifecycle_contract_test.dart test/rental_lifecycle_layout_test.dart \
  test/rental_mutation_recovery_test.dart
flutter test --no-pub test/planning_scope_contract_test.dart \
  test/replacement_consent_flow_test.dart --name disabled \
  --dart-define=SOKOUN_HOUSING_OFFERS=false \
  --dart-define=SOKOUN_CONDITION_REPORTS=false \
  --dart-define=SOKOUN_MOVE_OUT_NOTICES=false \
  --dart-define=SOKOUN_REPLACEMENTS=false
flutter build apk --debug --flavor dev --no-pub \
  --dart-define=SOKOUN_BYPASS_VERIFICATION=false
```

Use the SDK path above when `flutter` is not on PATH. The actual disabled-mode run set all twelve planning flags false; the four shown cover the five selected assertions. Fresh migration/system checks used `config.settings.test`; neither command reads production database settings.

## Boundaries and deployment

Routes/Gemini network responses, signing, payments and push are controlled test providers. The Gemini request shape was additionally checked against Google's public REST discovery schema. This proves neither live model entitlement nor account quota. No phone execution, iOS build, microphone permission, device push or deployed scheduler evidence is claimed. The native Android artifact is a debug build, not a release.

Group applications intentionally stop at owner approval under the approved single-tenant lease model. They create no lease or interest for the coordinator. Joint leases and group chat remain unsupported capabilities.

See [deployment settings and migration order](../../PLANNING_FEATURES_DEPLOYMENT.md). The companion app's `docs/sokoun_new_features_implementation_report.md` and `docs/sokoun_new_features_qa_checklist.md` contain the Arabic implementation report and remaining device/provider acceptance cases. The user owns server release.
