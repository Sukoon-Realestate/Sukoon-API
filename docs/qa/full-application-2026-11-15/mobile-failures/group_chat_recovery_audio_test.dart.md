# group_chat_recovery_audio_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/group_chat_recovery_audio_test.dart
```

## MOB-f7dfca3d20f9

protected restoration completes before events can overwrite saved composition

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_recovery_audio_test.dart 128:7      main.<fn>

```

## MOB-f5888aeb870b

permission denial offers settings and never sends a message

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_recovery_audio_test.dart 142:5      main.<fn>

```

## MOB-c7dac58cced0

finalizing recording produces an unsent preview and background cancels microphone

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                        _Array.single
test/group_chat_recovery_audio_test.dart 152:41  main.<fn>

```

## MOB-04090b784542

navigation stops a recording without upload or automatic send

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_recovery_audio_test.dart 166:7      main.<fn>

```

## MOB-9002a8c90a3a

mute serializes the pending write and failed mutation retains canonical preference

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: [true]
  Actual: []
   Which: at location [0] is [] which shorter than expected

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_recovery_audio_test.dart 181:7      main.<fn>

```
