# chat_property_sharing_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/chat_property_sharing_test.dart
```

## MOB-c69d7a39bc90

property without caption is protected and queued with its original identity

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/chat_property_sharing_test.dart 110:7          main.<fn>

```

## MOB-2d2459d4e19a

caption survives selection and storage failure restores the composition

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: ChatSharedProperty:<ChatSharedProperty(property-1, room-2, ChatPropertyAvailability.available, سكن بجوار الجامعة, , , 1500, monthly, غرفة ٢, false)>
  Actual: <null>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/chat_property_sharing_test.dart 136:7          main.<fn>

```

## MOB-80693febfd30

a recovered property needs a draft decision and discard preserves uncertain sends

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/chat_property_sharing_test.dart 161:7          main.<fn>

```

## MOB-5530d3475638

opening from details preserves recovered composition until the user resolves it

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: ChatSharedProperty:<ChatSharedProperty(property-1, room-2, ChatPropertyAvailability.available, سكن بجوار الجامعة, , , 1500, monthly, غرفة ٢, false)>
  Actual: <null>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/chat_property_sharing_test.dart 177:7          main.<fn>

```

## MOB-921e2399cfdd

reconciliation matches exact property and offer, not changed display fields

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                    _Array.single
test/chat_property_sharing_test.dart 193:45  main.<fn>

```

## MOB-e446e27539fd

withdrawn property is a definitive rejection with a useful message

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:collection                              ListBase.singleWhere
test/chat_property_sharing_test.dart 278:37  main.<fn>

```
