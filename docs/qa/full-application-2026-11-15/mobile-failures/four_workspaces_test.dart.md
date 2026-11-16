# four_workspaces_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/four_workspaces_test.dart
```

## MOB-31fb21702501

four spaces preserve legacy rental actor wire values

Result: `failure`.

```text
Expected: [
            WorkspaceTab:WorkspaceTab.home,
            WorkspaceTab:WorkspaceTab.saved,
            WorkspaceTab:WorkspaceTab.messages,
            WorkspaceTab:WorkspaceTab.housing,
            WorkspaceTab:WorkspaceTab.profile
          ]
  Actual: MappedListIterable<HomeTab, WorkspaceTab>:[
            WorkspaceTab:WorkspaceTab.home,
            WorkspaceTab:WorkspaceTab.saved,
            WorkspaceTab:WorkspaceTab.messages,
            WorkspaceTab:WorkspaceTab.visits,
            WorkspaceTab:WorkspaceTab.profile
          ]
   Which: at location [3] is WorkspaceTab:<WorkspaceTab.visits> instead of WorkspaceTab:<WorkspaceTab.housing>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/four_workspaces_test.dart 71:7                 main.<fn>

```

## MOB-acbb63893b6b

explicit guest choice survives authentication and is isolated by account and environment

Result: `failure`.

```text
Expected: AppWorkspace:<AppWorkspace.student>
  Actual: AppWorkspace:<AppWorkspace.individual>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/four_workspaces_test.dart 93:7                 main.<fn>

```

## MOB-79deaeaaf469

company selection ignores a late result and a cleared selection

Result: `failure`.

```text
Expected: 'b'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: b

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/four_workspaces_test.dart 127:7                main.<fn>

```

## MOB-a2206e6bd5a1

private company notebook scope never aliases personal notebook

Result: `failure`.

```text
Expected: 'a'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: a

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/four_workspaces_test.dart 151:7                main.<fn>

```

## MOB-4da573a8b501

company selection is isolated by environment

Result: `failure`.

```text
Expected: 'a'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: a

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/four_workspaces_test.dart 166:5                main.<fn>

```

## MOB-64be4ea647de

company tabs hide content during revalidation and revocation

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
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanySavedListsView": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:234:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 234
The test description was:
  company tabs hide content during revalidation and revocation
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: company tabs hide content during revalidation and revocation

```

## MOB-374753fec364

retained hidden company tabs do not fetch their own selector

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
Expected: <1>
  Actual: <0>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:287:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 287
The test description was:
  retained hidden company tabs do not fetch their own selector
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: retained hidden company tabs do not fetch their own selector

```

## MOB-3efc1f11bd54

hidden company content waits for its own scope to be visited

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
Expected: <1>
  Actual: <0>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:335:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 335
The test description was:
  hidden company content waits for its own scope to be visited
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: hidden company content waits for its own scope to be visited

```

## MOB-df1fccb91594

workspace chooser ar at 320.0 with large text

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
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "Card": [
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#14aaf]]),
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#14aaf]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:381:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 381
The test description was:
  workspace chooser ar at 320.0 with large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: workspace chooser ar at 320.0 with large text

```

## MOB-bd559e81f689

workspace chooser ar at 1024.0 with large text

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
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "Card": [
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#49da6]]),
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#49da6]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:381:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 381
The test description was:
  workspace chooser ar at 1024.0 with large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: workspace chooser ar at 1024.0 with large text

```

## MOB-0a8f639d57ad

workspace chooser en at 320.0 with large text

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
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "Card": [
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#6a64d]]),
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#6a64d]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:381:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 381
The test description was:
  workspace chooser en at 320.0 with large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: workspace chooser en at 320.0 with large text

```

## MOB-334af2cd69cd

workspace chooser en at 1024.0 with large text

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
  Actual: _TypeWidgetFinder:<Found 2 widgets with type "Card": [
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#e68d0]]),
            Card(dependencies: [InheritedCupertinoTheme, _InheritedTheme,
_LocalizationsScope-[GlobalKey#e68d0]]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart:381:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/four_workspaces_test.dart line 381
The test description was:
  workspace chooser en at 1024.0 with large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: workspace chooser en at 1024.0 with large text

```
