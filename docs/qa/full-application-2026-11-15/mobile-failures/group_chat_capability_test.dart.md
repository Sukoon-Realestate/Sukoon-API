# group_chat_capability_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/group_chat_capability_test.dart
```

## MOB-fea4d2530263

server denies group access before history, draft restoration or socket

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_capability_test.dart 60:7           main.<fn>

```
