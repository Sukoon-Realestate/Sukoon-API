# living_lab_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/living_lab_test.dart
```

## MOB-180bf61ca1b9

scenario creates a separately receipted child and sends only the chosen assumption

Result: `failure`.

```text
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/living_lab_test.dart 249:7                     main.<fn>

```

## MOB-98ee0f91c9a1

writes reauthorize and require the exact command receipt

Result: `failure`.

```text
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/living_lab_test.dart 409:5                     main.<fn>

```
