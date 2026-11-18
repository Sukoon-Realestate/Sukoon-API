# Sprint 4 first tranche — 18 November 2026

Successful commands (exit zero):

1. API backend: `make test-connected-acceptance BASELINE_OUT=/private/tmp/sprint4-acceptance-20261118`.
   **10 passed**, 70.68 seconds. Two connected scenarios (MVP/restoration), eight
   client-boundary cases. The existing Django deprecation/static-directory warnings
   remain. `http-acceptance.log.gz` is the successful terminal output.
2. Mobile app directory: `make sprint4AcceptanceToolsCheck`.
   **7 passed**. `reconciler-tests.log.gz` contains terminal output.
3. Mobile `tool/qa/reconcile_connected_acceptance.py` with the current API backend,
   baseline `inventory/control_execution_cases.jsonl`, both receipts in this folder
   and `--output ledger-overlay.json`. **4 backend entries partially observed**,
   6,445 entries without new observations. Original ledger unchanged.

The two receipts contain 16 real HTTP exchanges each and six completed behavior
assertions. No APIClient, forced authentication, hosted service or provider was
used. Pytest created and destroyed its own database; no shared database was
migrated. Replay uses a copy of the first synthetic account's cookie jar before
logout and confirms that the captured access cookie is rejected afterward.

The receipt source hashes cover the enumerated test/client/authentication/URL
files, not the entire dependency tree. `source-manifest.json` additionally records
the reconciler and test source used for this evidence. Hashes bind these local
artifacts; they are not independent hosted attestation.

This is backend-entry evidence only. No mobile controls or hosted/provider/device
acceptance are closed by this overlay. Sprint 4 remains in progress. Sprint 3
publication preceded this work: API main `7337c418`, mobile main `f2c87891`.
