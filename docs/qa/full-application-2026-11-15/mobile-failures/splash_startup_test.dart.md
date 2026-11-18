# splash_startup_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/splash_startup_test.dart
```

## MOB-65adf1917385

renders splash before service setup and waits for it (reduced motion: false)

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [exception_error] not found
[🌎 Easy Localization] [WARNING] Localization key [owner_retry_action] not found
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: No element

When the exception was thrown, this was the stack:
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      WidgetController.widget (package:flutter_test/src/controller.dart:828:30)
#2      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart:89:42)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  renders splash before service setup and waits for it (reduced motion: false)
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: renders splash before service setup and waits for it (reduced motion: false)

```

## MOB-fdaa47e1cd97

renders splash before service setup and waits for it (reduced motion: true)

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [exception_error] not found
[🌎 Easy Localization] [WARNING] Localization key [owner_retry_action] not found
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: No element

When the exception was thrown, this was the stack:
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      WidgetController.widget (package:flutter_test/src/controller.dart:828:30)
#2      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart:89:42)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  renders splash before service setup and waits for it (reduced motion: true)
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: renders splash before service setup and waits for it (reduced motion: true)

```

## MOB-72c6741500bd

fast startup selects without waiting for decorative writing: Welcome once

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: an object with length of <1>
  Actual: []
   Which: has length of <0>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart:245:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart line 245
The test description was:
  fast startup selects without waiting for decorative writing: Welcome once
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: fast startup selects without waiting for decorative writing: Welcome once

```

## MOB-283c37ce12a7

fast startup selects without waiting for decorative writing: Home once

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: an object with length of <1>
  Actual: []
   Which: has length of <0>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart:245:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart line 245
The test description was:
  fast startup selects without waiting for decorative writing: Home once
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: fast startup selects without waiting for decorative writing: Home once

```

## MOB-0807673b9634

slow startup holds completed logo until session restoration finishes

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: No element

When the exception was thrown, this was the stack:
#0      Iterable.single (dart:core/iterable.dart:694:25)
#1      WidgetController.widget (package:flutter_test/src/controller.dart:828:30)
#2      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/splash_startup_test.dart:269:40)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  slow startup holds completed logo until session restoration finishes
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: slow startup holds completed logo until session restoration finishes

```
