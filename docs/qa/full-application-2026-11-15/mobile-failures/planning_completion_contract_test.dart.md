# planning_completion_contract_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/planning_completion_contract_test.dart
```

## MOB-c0472c0ca005

join creation binds the receipt to its new request and checks the group separately

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/planning_completion_contract_test.dart 68:7    main.<fn>

```
