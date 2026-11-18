# workspace_navigation_clearance_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/workspace_navigation_clearance_test.dart
```

## MOB-c998291d87b4

last company selector action clears navigation ar large text

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "ListTile" that are ancestors of widgets with text "Company
19": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last company selector action clears navigation ar large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last company selector action clears navigation ar large text

```

## MOB-b7c5a22ee465

last company saved lists action clears navigation ar large text

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "ListTile" that are ancestors of widgets with text "Company
19": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last company saved lists action clears navigation ar large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last company saved lists action clears navigation ar large text

```

## MOB-e7c08e1efe76

last owner group applications action clears navigation ar large text

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
#3      Iterable.isEmpty (dart:core/iterable.dart:560:33)
#4      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2094:18)
#5      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#6      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#7      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#8      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#9      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#10     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  last owner group applications action clears navigation ar large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last owner group applications action clears navigation ar large text

```

## MOB-df76efaa6f8c

last owner housing offers action clears navigation ar large text

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following ArgumentError was thrown running a test:
Invalid argument(s): Type WorkspaceCubit is already registered inside GetIt.

When the exception was thrown, this was the stack:
#0      throwIfNot (package:get_it/get_it_impl.dart:14:19)
#1      _GetItImplementation._register (package:get_it/get_it_impl.dart:2005:11)
#2      _GetItImplementation.registerSingleton (package:get_it/get_it_impl.dart:1206:5)
#3      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:192:22)
#4      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#5      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last owner housing offers action clears navigation ar large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last owner housing offers action clears navigation ar large text

```

## MOB-f2ac81c15bf0

student last action en 320.0 text 2.0

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
#7      WidgetController.drag (package:flutter_test/src/controller.dart:1602:31)
#8      _scrollToEnd (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:419:18)
#9      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:122:17)
<asynchronous suspension>
#10     testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#11     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  student last action en 320.0 text 2.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: student last action en 320.0 text 2.0

```

## MOB-a6355b3bd20d

last company selector action clears navigation en large text

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "ListTile" that are ancestors of widgets with text "Company
19": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last company selector action clears navigation en large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last company selector action clears navigation en large text

```

## MOB-88c2893cb0d6

last company saved lists action clears navigation en large text

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "ListTile" that are ancestors of widgets with text "Company
19": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last company saved lists action clears navigation en large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last company saved lists action clears navigation en large text

```

## MOB-d86b5f3fba9d

last owner group applications action clears navigation en large text

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
#0      Iterable.last (dart:core/iterable.dart:679:7)
#1      _LastFinderMixin.filter (package:flutter_test/src/finders.dart:1410:28)
#3      Iterable.isEmpty (dart:core/iterable.dart:560:33)
#4      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2094:18)
#5      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#6      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#7      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#8      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:275:11)
<asynchronous suspension>
#9      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#10     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  last owner group applications action clears navigation en large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last owner group applications action clears navigation en large text

```

## MOB-da0a775d0f65

last owner housing offers action clears navigation en large text

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following ArgumentError was thrown running a test:
Invalid argument(s): Type WorkspaceCubit is already registered inside GetIt.

When the exception was thrown, this was the stack:
#0      throwIfNot (package:get_it/get_it_impl.dart:14:19)
#1      _GetItImplementation._register (package:get_it/get_it_impl.dart:2005:11)
#2      _GetItImplementation.registerSingleton (package:get_it/get_it_impl.dart:1206:5)
#3      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:192:22)
#4      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#5      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  last owner housing offers action clears navigation en large text
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: last owner housing offers action clears navigation en large text

```

## MOB-7064b9693297

failed service gate retry remains tappable

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "TextButton" that are ancestors of widgets with text "حاول مرة
أخرى": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:356:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  failed service gate retry remains tappable
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: failed service gate retry remains tappable

```

## MOB-1fda33ed4028

company access recovery clears navigation on a short screen

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
The following assertion was thrown running a test:
The finder "Found 0 widgets with type "TextButton" that are ancestors of widgets with text "حاول مرة
أخرى": []" (used in a call to "getTopLeft()") could not find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getTopLeft (package:flutter_test/src/controller.dart:1963:12)
#2      WidgetController.getRect (package:flutter_test/src/controller.dart:2347:23)
#3      _expectClear (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:429:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/workspace_navigation_clearance_test.dart:405:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  company access recovery clears navigation on a short screen
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: company access recovery clears navigation on a short screen

```
