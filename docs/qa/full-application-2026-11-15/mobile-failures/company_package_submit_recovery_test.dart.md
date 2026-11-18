# company_package_submit_recovery_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_package_submit_recovery_test.dart
```

## MOB-90324d49fa2c

approved revision 5 restores after login and clears exact historical receipt 4 with GET only

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
The following TestFailure was thrown running a test:
Expected: empty
  Actual: [Instance of 'FeatureTestRequest']

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_package_submit_recovery_test.dart:165:7)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_package_submit_recovery_test.dart line 165
The test description was:
  approved revision 5 restores after login and clears exact historical receipt 4 with GET only
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: approved revision 5 restores after login and clears exact historical receipt 4 with GET only

```
