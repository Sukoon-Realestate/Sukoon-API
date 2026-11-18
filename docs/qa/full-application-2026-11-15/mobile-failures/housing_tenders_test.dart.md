# housing_tenders_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/housing_tenders_test.dart
```

## MOB-89752108efea

an exact own consent carries digest and no proxy identity

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/housing_tenders_test.dart 166:5                main.<fn>

```
