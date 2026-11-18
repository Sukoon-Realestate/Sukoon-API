# dashboard_consistency_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/dashboard_consistency_test.dart
```

## MOB-ac59dd678590

individual dashboard picker cancels without losing the body

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#42f81]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#42f81]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:255:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 255
The test description was:
  individual dashboard picker cancels without losing the body
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: individual dashboard picker cancels without losing the body

```

## MOB-e56674ca37ad

owner dashboard picker cancels without losing the body

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#7c686]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#7c686]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:255:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 255
The test description was:
  owner dashboard picker cancels without losing the body
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: owner dashboard picker cancels without losing the body

```

## MOB-ccd3ebb60727

student dashboard picker cancels without losing the body

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#198c6]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#198c6]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:255:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 255
The test description was:
  student dashboard picker cancels without losing the body
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: student dashboard picker cancels without losing the body

```

## MOB-bfacd742b1a9

dashboard company active=false ar dark=false 390.0 text=1.0

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
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyMembershipsEmptyState": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:196:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 196
The test description was:
  dashboard company active=false ar dark=false 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=false ar dark=false 390.0 text=1.0

```

## MOB-597545547b71

dashboard company active=false ar dark=true 390.0 text=1.0

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
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyMembershipsEmptyState": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:196:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 196
The test description was:
  dashboard company active=false ar dark=true 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=false ar dark=true 390.0 text=1.0

```

## MOB-1f559a963a9a

dashboard company active=false en dark=false 390.0 text=1.0

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
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyMembershipsEmptyState": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:196:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 196
The test description was:
  dashboard company active=false en dark=false 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=false en dark=false 390.0 text=1.0

```

## MOB-cf17776b4bee

dashboard company active=false en dark=true 390.0 text=1.0

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
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyMembershipsEmptyState": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:196:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 196
The test description was:
  dashboard company active=false en dark=true 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=false en dark=true 390.0 text=1.0

```

## MOB-06678ce89795

dashboard company active=true ar dark=false 320.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=false 320.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=false 320.0 text=2.0

```

## MOB-a16dc72e7d9f

dashboard company active=true ar dark=false 390.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=false 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=false 390.0 text=1.0

```

## MOB-ff175e4d5980

dashboard company active=true ar dark=false 430.0 text=1.3

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=false 430.0 text=1.3
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=false 430.0 text=1.3

```

## MOB-15b9fe1b577c

dashboard company active=true ar dark=false 768.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=false 768.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=false 768.0 text=2.0

```

## MOB-2e7ad7504344

dashboard company active=true ar dark=false 1366.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=false 1366.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=false 1366.0 text=1.0

```

## MOB-d7b53c3eee3d

dashboard company active=true ar dark=true 320.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=true 320.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=true 320.0 text=2.0

```

## MOB-18f38fda7a1c

dashboard company active=true ar dark=true 390.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=true 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=true 390.0 text=1.0

```

## MOB-a4e60a403a50

dashboard company active=true ar dark=true 430.0 text=1.3

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=true 430.0 text=1.3
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=true 430.0 text=1.3

```

## MOB-30b7e26891b8

dashboard company active=true ar dark=true 768.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=true 768.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=true 768.0 text=2.0

```

## MOB-6dff87884b73

dashboard company active=true ar dark=true 1366.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true ar dark=true 1366.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true ar dark=true 1366.0 text=1.0

```

## MOB-0b0ae1ef8820

dashboard company active=true en dark=false 320.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=false 320.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=false 320.0 text=2.0

```

## MOB-255d6b4cfff3

dashboard company active=true en dark=false 390.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=false 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=false 390.0 text=1.0

```

## MOB-dae6f5a7b79d

dashboard company active=true en dark=false 430.0 text=1.3

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=false 430.0 text=1.3
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=false 430.0 text=1.3

```

## MOB-2ba820d10191

dashboard company active=true en dark=false 768.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=false 768.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=false 768.0 text=2.0

```

## MOB-6bfe50c96895

dashboard company active=true en dark=false 1366.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=false 1366.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=false 1366.0 text=1.0

```

## MOB-7f0a18803900

dashboard company active=true en dark=true 320.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=true 320.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=true 320.0 text=2.0

```

## MOB-b9fa241d5f36

dashboard company active=true en dark=true 390.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=true 390.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=true 390.0 text=1.0

```

## MOB-1f6232eda7ab

dashboard company active=true en dark=true 430.0 text=1.3

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=true 430.0 text=1.3
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=true 430.0 text=1.3

```

## MOB-70c35aba458d

dashboard company active=true en dark=true 768.0 text=2.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=true 768.0 text=2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=true 768.0 text=2.0

```

## MOB-9075203a8d51

dashboard company active=true en dark=true 1366.0 text=1.0

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:166:19)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 166
The test description was:
  dashboard company active=true en dark=true 1366.0 text=1.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: dashboard company active=true en dark=true 1366.0 text=1.0

```

## MOB-50788f64c4dc

company dashboard picker cancels without losing the body

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#5aebf]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#5aebf]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:255:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 255
The test description was:
  company dashboard picker cancels without losing the body
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: company dashboard picker cancels without losing the body

```

## MOB-f531a1a7304f

owner workspace controls remain available while dashboard read loads and fails

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#85b7d]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#85b7d]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart:372:7)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/dashboard_consistency_test.dart line 372
The test description was:
  owner workspace controls remain available while dashboard read loads and fails
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: owner workspace controls remain available while dashboard read loads and fails

```
