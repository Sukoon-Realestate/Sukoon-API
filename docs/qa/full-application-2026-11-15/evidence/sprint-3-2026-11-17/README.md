# Sprint 3 first recovery batch — 17 November 2026

| Run | Result | Raw events |
|---|---|---|
| Original three files, MVP, before repair | 166 pass / 7 errors, unsuccessful terminal | [events](before-mvp.jsonl.gz) |
| Original company/payment files, full mode, before repair | 15 pass, successful terminal | [events](before-full-company.jsonl.gz) |
| Intermediate MVP run | 177 pass / 2 toast-timer errors / 1 skip | [events](diagnostic-toast-cleanup.jsonl.gz) |
| Final MVP: repaired files + release-scope regressions | 179 pass / 1 intentional company-workspace skip | [events](after-mvp.jsonl.gz) |
| Final full-release: same files | 180 pass / no skips | [events](after-full.jsonl.gz) |

Both final streams have an explicit successful terminal event and no active tests. [Machine-readable results](results.json), [seven case dispositions](case-dispositions.json), [source hashes](sources.json), and [clean focused analysis](focused-analysis.txt).

The initial company failures are not evidence that the company feature should be enabled in MVP. Their original code passes unchanged under the full-release flag. Restored tests now explicitly cover refusal in the default build and retained behavior in the full build. The owner recovery variant keeps double-submit/timeout protection exercised in both configurations.

The timer diagnostic was caused by new error-path coverage leaving the read-error toast active. The test now dismisses its own toast after asserting the refusal and before Flutter checks timers. Outer tearDown alone was too late. No Flutter invariant or product error handler was disabled.

## Repeat

From `sokoun/apps/sokoun_app`, `make sprint3RegressionCheck` runs the same four files under both explicit release modes. Individual JSON runs use:

```
flutter test --no-pub --timeout 60s --reporter json --dart-define=SUKOON_MVP=true test/rental_mock_provider_test.dart test/rental_listing_categories_test.dart test/company_role_work_status_test.dart test/mvp_scope_test.dart
flutter test --no-pub --timeout 60s --reporter json --dart-define=SUKOON_MVP=false test/rental_mock_provider_test.dart test/rental_listing_categories_test.dart test/company_role_work_status_test.dart test/mvp_scope_test.dart
```

From the API repository, the bounded runner accepts `--mode mvp` or `--mode full`. It retains the existing process-group wall timeout and now writes JSON event counts, active tests and a required terminal-success field. Exit 125 rejects a zero-exit incomplete event stream; skips remain separate. The actual company MVP runner result is in `../../reruns/20261117-151532/`. Four stdlib unit tests cover unfinished streams, active tests, hidden setup errors and separate skip counts: run `python3 -m unittest test_mobile_run_report.py` from this QA directory.

No mobile product source or release defaults were changed in this batch. Concurrent user edits to shared headers/profile/owner controls were preserved. These are widget/contract tests, not device/provider/hosted acceptance. The other 490 historical failure records and a fresh successful full app/core suite still require reconciliation; no whole-suite or Sprint 3 completion claim is made.
