# student_housing_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/student_housing_test.dart
```

## MOB-5e40f83394b3

fresh capability and exact receipt bind academic mutation to stable intent

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/student_housing_test.dart 234:7                main.<fn>

```
