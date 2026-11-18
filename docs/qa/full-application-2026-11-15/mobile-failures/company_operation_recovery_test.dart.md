# company_operation_recovery_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_operation_recovery_test.dart
```

## MOB-786b2c318d75

explicit closure sends identity and clears only exact receipt: false

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
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_operation_recovery_test.dart:199:14)
<asynchronous suspension>
#2      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#3      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  explicit closure sends identity and clears only exact receipt: false
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: explicit closure sends identity and clears only exact receipt: false

```

## MOB-e15a88502972

explicit closure sends identity and clears only exact receipt: true

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
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_operation_recovery_test.dart:199:14)
<asynchronous suspension>
#2      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#3      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  explicit closure sends identity and clears only exact receipt: true
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: explicit closure sends identity and clears only exact receipt: true

```
