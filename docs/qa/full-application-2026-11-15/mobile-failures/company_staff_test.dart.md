# company_staff_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_staff_test.dart
```

## MOB-02608413209a

staff creation cannot accept a receipt from another company

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                            List.last
test/company_staff_test.dart 111:32  main.<fn>

```

## MOB-b49dd912e350

a late staff response cannot replace the newly selected company

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: 'company-b'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: company-b

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_staff_test.dart 303:7                  main.<fn>

```
