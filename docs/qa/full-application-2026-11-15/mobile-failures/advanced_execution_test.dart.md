# advanced_execution_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/advanced_execution_test.dart
```

## MOB-02aecdb4597f

lost ACK stays unknown and mounted execution clears on account replacement

Result: `failure`.

```text
Expected: RentalSubmissionResult:<RentalSubmissionResult.unknown>
  Actual: RentalSubmissionResult:<RentalSubmissionResult.rejected>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/advanced_execution_test.dart 350:7             main.<fn>

```

## MOB-74063a05c445

new execution child accepts its own revision while checking exact source

Result: `failure`.

```text
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/advanced_execution_test.dart 394:7             main.<fn>

```

## MOB-0dd936420a25

bounded constructor keeps unknown outcome distinct from infeasibility

Result: `failure`.

```text
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/advanced_execution_test.dart 451:7             main.<fn>

```
