# group_chat_upload_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/group_chat_upload_test.dart
```

## MOB-6a9724bb2691

partial upload failure never publishes a partial image bundle; retry preserves identities

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.first
test/group_chat_upload_test.dart 103:41  main.<fn>

```

## MOB-85a28faa6d67

send keeps its caption, reply and complete bundle fixed during upload

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.first
test/group_chat_upload_test.dart 127:41  main.<fn>

```

## MOB-d904abf40019

ambiguous upload checks server identity instead of repeating multipart data

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_upload_test.dart 152:7              main.<fn>

```

## MOB-5f91f1f10f75

confirmed missing upload retries the retained original file and UUID

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_upload_test.dart 202:38  main.<fn>

```

## MOB-f36d30c84ecd

the composer limit counts Unicode code points rather than UTF-16 units

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: an object with length of <1>
  Actual: []
   Which: has length of <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_upload_test.dart 222:7              main.<fn>

```
