# advanced_privacy_capability_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/advanced_privacy_capability_test.dart
```

## MOB-85aa38de6ebc

privacy withdrawal remains available for exact historical lab with disabled planning

Result: `failure`.

```text
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/advanced_privacy_capability_test.dart 36:7     main.<fn>

```
