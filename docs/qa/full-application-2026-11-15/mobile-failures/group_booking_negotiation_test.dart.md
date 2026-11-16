# group_booking_negotiation_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/group_booking_negotiation_test.dart
```

## MOB-d91cf2124709

history and disabled own actions en at 320 with large text

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded en
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
[🌎 Easy Localization] [DEBUG] Load Localization Delegate
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: No element

When the exception was thrown, this was the stack:
#0      Iterable.first (dart:core/iterable.dart:663:7)
#1      _FirstFinderMixin.filter (package:flutter_test/src/finders.dart:1383:28)
#3      _AncestorFinderMixin.allCandidates (package:flutter_test/src/finders.dart:1857:49)
#4      FinderBase.evaluate (package:flutter_test/src/finders.dart:1030:76)
#5      WidgetController.widgetList (package:flutter_test/src/controller.dart:848:19)
#6      WidgetController._maybeViewOf (package:flutter_test/src/controller.dart:795:34)
#7      WidgetController.tap (package:flutter_test/src/controller.dart:1078:31)
#8      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/group_booking_negotiation_test.dart:274:22)
<asynchronous suspension>
#9      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#10     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  history and disabled own actions en at 320 with large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: history and disabled own actions en at 320 with large text

```
