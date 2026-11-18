# tenant_property_details_screen_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/tenant_property_details_screen_test.dart
```

## MOB-6f11dbacf726

shows the exception view when no cached details exist

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
[🌎 Easy Localization] [WARNING] Localization key [tenant_filter_property_details] not found
[🌎 Easy Localization] [WARNING] Localization key [content_loading] not found
[🌎 Easy Localization] [WARNING] Localization key [check_internet] not found
[🌎 Easy Localization] [WARNING] Localization key [check_internet] not found
[🌎 Easy Localization] [WARNING] Localization key [check_internet] not found
[🌎 Easy Localization] [WARNING] Localization key [owner_retry_action] not found
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "AppBar": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/tenant_property_details_screen_test.dart:375:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/tenant_property_details_screen_test.dart line 375
The test description was:
  shows the exception view when no cached details exist
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: shows the exception view when no cached details exist

```
