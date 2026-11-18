# ux60_chat_suggested_draft_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/ux60_chat_suggested_draft_test.dart
```

## MOB-5b1b7f53a6a4

suggestion preserves the recovered draft and never transmits

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: 'Existing private draft'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: Existing p ...

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/ux60_chat_suggested_draft_test.dart 52:7       main.<fn>

```
