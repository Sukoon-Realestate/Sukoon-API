# mobile_dev_handoff_integration_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/mobile_dev_handoff_integration_test.dart
```

## MOB-b047d83e8e9d

failed revenue loads recover through pull refresh

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
The following TestFailure was thrown running a test:
Expected: no matching candidates
  Actual: _TextWidgetFinder:<Found 1 widget with text "Try again": [
            Text("Try again", inherit: true, color: Color(alpha: 1.0000, red: 0.9882, green: 0.9843,
blue: 0.9686, colorSpace: ColorSpace.sRGB), family: SokounPlex, familyFallback: [], size: 13.0,
weight: 700, dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: means one was found but none were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/mobile_dev_handoff_integration_test.dart:407:5)
<asynchronous suspension>
#5      testWidgetsWithToasts.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/helpers/toast_test_widgets.dart:17:9)
<asynchronous suspension>
#6      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#7      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/mobile_dev_handoff_integration_test.dart line 407
The test description was:
  failed revenue loads recover through pull refresh
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: failed revenue loads recover through pull refresh

```

## MOB-5e70c9d46daa

owner Profile opens API-backed revenue

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
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      WidgetController.element (package:flutter_test/src/controller.dart:888:30)
#2      WidgetController.ensureVisible (package:flutter_test/src/controller.dart:2389:32)
#3      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/mobile_dev_handoff_integration_test.dart:423:18)
<asynchronous suspension>
#4      testWidgetsWithToasts.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/helpers/toast_test_widgets.dart:17:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  owner Profile opens API-backed revenue
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: owner Profile opens API-backed revenue

```
