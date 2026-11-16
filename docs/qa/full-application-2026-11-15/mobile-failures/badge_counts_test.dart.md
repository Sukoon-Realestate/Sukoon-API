# badge_counts_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/badge_counts_test.dart
```

## MOB-31362b687da7

group send, socket echoes and reader receipts never fetch unread counts

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [check_internet] not found
[🌎 Easy Localization] [WARNING] Localization key [check_internet] not found
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                           _Array.single
test/badge_counts_test.dart 255:52  main.<fn>

```
