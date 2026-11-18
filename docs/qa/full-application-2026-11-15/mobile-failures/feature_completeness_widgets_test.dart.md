# feature_completeness_widgets_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/feature_completeness_widgets_test.dart
```

## MOB-b22ef65c4b48

sessions show device labels and revoking another device retains current account

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
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
#0      Iterable.last (dart:core/iterable.dart:679:7)
#1      _LastFinderMixin.filter (package:flutter_test/src/finders.dart:1410:28)
#3      Iterable.single (dart:core/iterable.dart:694:13)
#4      WidgetController.element (package:flutter_test/src/controller.dart:888:30)
#5      WidgetController.ensureVisible (package:flutter_test/src/controller.dart:2389:32)
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/feature_completeness_widgets_test.dart:182:20)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  sessions show device labels and revoking another device retains current account
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: sessions show device labels and revoking another device retains current account

```
