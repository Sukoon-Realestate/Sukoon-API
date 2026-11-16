# workspace_switcher_design_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/workspace_switcher_design_test.dart
```

## MOB-ec00b7889a2f

picker escapes the home hero theme dark=false width=390.0

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#f7f6f]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#f7f6f]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart:210:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart line 210
The test description was:
  picker escapes the home hero theme dark=false width=390.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: picker escapes the home hero theme dark=false width=390.0

```

## MOB-938db82bcbae

picker escapes the home hero theme dark=false width=1024.0

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#918b5]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#918b5]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart:210:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart line 210
The test description was:
  picker escapes the home hero theme dark=false width=1024.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: picker escapes the home hero theme dark=false width=1024.0

```

## MOB-e380ddf0d2c9

picker escapes the home hero theme dark=true width=390.0

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#35c71]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#35c71]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart:210:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart line 210
The test description was:
  picker escapes the home hero theme dark=true width=390.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: picker escapes the home hero theme dark=true width=390.0

```

## MOB-a4f4f8e33899

picker escapes the home hero theme dark=true width=1024.0

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
Expected: exactly 4 matching candidates
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "WorkspaceOption": [
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#d16a2]]),
            WorkspaceOption(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#d16a2]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart:210:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart line 210
The test description was:
  picker escapes the home hero theme dark=true width=1024.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: picker escapes the home hero theme dark=true width=1024.0

```

## MOB-7aa2d69a0ffb

switching away does not refocus the retained inactive dashboard

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
#8      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_switcher_design_test.dart:261:20)
<asynchronous suspension>
#9      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#10     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  switching away does not refocus the retained inactive dashboard
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: switching away does not refocus the retained inactive dashboard

```
