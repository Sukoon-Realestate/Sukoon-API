# transition_network_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/transition_network_test.dart
```

## MOB-b3d7e596522d

child run revision is independent of reviewed parent revision

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/transition_network_test.dart 199:7             main.<fn>

```

## MOB-a973d8fe918f

execution proposal receipt must belong to this transition source

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/transition_network_test.dart 258:7             main.<fn>

```

## MOB-c2cac505b7a2

interest binds own exact snapshot and cannot submit proxy identity

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <true>
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/transition_network_test.dart 302:7             main.<fn>

```
