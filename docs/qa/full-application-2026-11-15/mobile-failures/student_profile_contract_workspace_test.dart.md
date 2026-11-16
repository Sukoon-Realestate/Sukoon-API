# student_profile_contract_workspace_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/student_profile_contract_workspace_test.dart
```

## MOB-6e6fcbbf5b07

ar student profile preserves contracts workspace

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: AppWorkspace:<AppWorkspace.student>
  Actual: AppWorkspace:<AppWorkspace.individual>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:75:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart line 75
The test description was:
  ar student profile preserves contracts workspace
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: ar student profile preserves contracts workspace

```

## MOB-6edd93c459e5

ar individual profile preserves contracts workspace

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
#1      WidgetController.element (package:flutter_test/src/controller.dart:888:30)
#2      WidgetController.dragUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2489:38)
<asynchronous suspension>
#3      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#4      WidgetController.scrollUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2439:7)
<asynchronous suspension>
#5      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#6      _scrollProfileTo (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:285:3)
<asynchronous suspension>
#7      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:86:11)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  ar individual profile preserves contracts workspace
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: ar individual profile preserves contracts workspace

```

## MOB-cb093f9d67d0

ar company profile keeps its company housing entry

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
#1      WidgetController.element (package:flutter_test/src/controller.dart:888:30)
#2      WidgetController.dragUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2489:38)
<asynchronous suspension>
#3      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#4      WidgetController.scrollUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2439:7)
<asynchronous suspension>
#5      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#6      _scrollProfileTo (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:285:3)
<asynchronous suspension>
#7      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:162:7)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  ar company profile keeps its company housing entry
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: ar company profile keeps its company housing entry

```

## MOB-80519e415c6b

en student profile preserves contracts workspace

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: AppWorkspace:<AppWorkspace.student>
  Actual: AppWorkspace:<AppWorkspace.individual>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:75:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart line 75
The test description was:
  en student profile preserves contracts workspace
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: en student profile preserves contracts workspace

```

## MOB-ccdc3b5dd57d

en individual profile preserves contracts workspace

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
#2      WidgetController.dragUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2489:38)
<asynchronous suspension>
#3      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#4      WidgetController.scrollUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2439:7)
<asynchronous suspension>
#5      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#6      _scrollProfileTo (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:285:3)
<asynchronous suspension>
#7      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:86:11)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  en individual profile preserves contracts workspace
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: en individual profile preserves contracts workspace

```

## MOB-0f0d7a9a5390

en company profile keeps its company housing entry

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
#2      WidgetController.dragUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2489:38)
<asynchronous suspension>
#3      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#4      WidgetController.scrollUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2439:7)
<asynchronous suspension>
#5      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#6      _scrollProfileTo (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:285:3)
<asynchronous suspension>
#7      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/student_profile_contract_workspace_test.dart:162:7)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  en company profile keeps its company housing entry
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: en company profile keeps its company housing entry

```
