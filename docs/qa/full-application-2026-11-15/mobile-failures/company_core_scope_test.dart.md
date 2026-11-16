# company_core_scope_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_core_scope_test.dart
```

## MOB-ff6062ba3e17

late company A response cannot replace company B context

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: 'company-b'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: company-b

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_core_scope_test.dart 83:5              main.<fn>

```
