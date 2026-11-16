# company_role_populated_layout_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_role_populated_layout_test.dart
```

## MOB-b3fe247a9dfc

populated admin ar 320.0

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

Warning: A call to tap() with finder "Found 1 widget with text "إضافة موظف": [
  Text("إضافة موظف", inherit: true, family: SokounPlex, familyFallback: [], weight: 400, height: 1.6x, textAlign: start, dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery, _ScrollableScope]),
]" derived an Offset (Offset(184.8, 746.5)) that would not hit test on the specified widget.
Maybe the widget is actually off-screen, or another widget is obscuring it, or the widget cannot receive pointer events.
The finder corresponds to this RenderBox: RenderParagraph#981d8 relayoutBoundary=up37
The hit test result at that offset is: HitTestResult(RenderDecoratedBox#237b9@Offset(168.8, 10.5), RenderConstrainedBox#30a12@Offset(168.8, 10.5), RenderPadding#46493@Offset(184.8, 22.5), RenderMouseRegion#b0be7@Offset(184.8, 22.5), RenderPointerListener#a68bf@Offset(184.8, 22.5), RenderSemanticsGestureHandler#5b864@Offset(184.8, 22.5), RenderOpacity#e7f45@Offset(184.8, 22.5), RenderPointerListener#7ae90@Offset(184.8, 22.5), RenderSemanticsGestureHandler#56775@Offset(184.8, 22.5), RenderPointerListener#1c8fc@Offset(184.8, 22.5), RenderAnimatedOpacity#79716@Offset(184.8, 22.5), RenderPositionedBox#abe20@Offset(184.8, 22.5), RenderRepaintBoundary#e4e27@Offset(184.8, 22.5), RenderIndexedSemantics#a173c@Offset(184.8, 22.5), RenderSliverList@(mainAxis: 141.5, crossAxis: 184.77999114990234), RenderSliverPadding@(mainAxis: 141.5, crossAxis: 184.77999114990234), RenderShrinkWrappingViewport#8b0bd@Offset(184.8, 22.5), RenderIgnorePointer#4eba7@Offset(184.8, 22.5), RenderSemanticsAnnotations#6494d@Offset(184.8, 22.5), RenderPointerListener#1599e@Offset(184.8, 22.5), RenderSemanticsGestureHandler#f45cd@Offset(184.8, 22.5), RenderPointerListener#459fb@Offset(184.8, 22.5), _RenderScrollSemantics#b64bc@Offset(184.8, 22.5), RenderClipRect#382c1@Offset(184.8, 22.5), RenderConstrainedBox#6f139@Offset(184.8, 22.5), RenderPadding#05c34@Offset(184.8, 22.5), RenderPositionedBox#c1212@Offset(184.8, 746.5), _RenderTheater#bf77e@Offset(184.8, 746.5), RenderAbsorbPointer#60ef1@Offset(184.8, 746.5), RenderPointerListener#b67db@Offset(184.8, 746.5), RenderSemanticsAnnotations#f7fd9@Offset(184.8, 746.5), RenderCustomPaint#93b4c@Offset(184.8, 746.5), RenderSemanticsAnnotations#7d89d@Offset(184.8, 746.5), RenderSemanticsAnnotations#877e6@Offset(184.8, 746.5), RenderSemanticsAnnotations#71c94@Offset(184.8, 746.5), RenderTapRegionSurface#79535@Offset(184.8, 746.5), RenderSemanticsAnnotations#a5f49@Offset(184.8, 746.5), RenderSemanticsAnnotations#9c04c@Offset(184.8, 746.5), HitTestEntry<HitTestTarget>#c8a50(_ReusableRenderView#278d9), HitTestEntry<HitTestTarget>#d3b5e(<AutomatedTestWidgetsFlutterBinding>))
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2165:25)
#1      WidgetController.getCenter (package:flutter_test/src/controller.dart:1947:12)
#2      WidgetController.tap (package:flutter_test/src/controller.dart:1080:7)
#3      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:124:24)
<asynchronous suspension>
#4      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#5      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
#6      StackZoneSpecification._registerCallback.<anonymous closure> (package:stack_trace/src/stack_zone_specification.dart:114:42)
<asynchronous suspension>
To silence this warning, pass "warnIfMissed: false" to "tap()".
To make this warning fatal, set WidgetController.hitTestWarningShouldBeFatal to true.

══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyStaffForm": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:126:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart line 126
The test description was:
  populated admin ar 320.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated admin ar 320.0

```

## MOB-2c098ed5c1fe

populated admin en 1024.0

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
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:139:9)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  populated admin en 1024.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated admin en 1024.0

```

## MOB-cd34952d1f56

populated coordinator ar 320.0

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
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:139:9)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  populated coordinator ar 320.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated coordinator ar 320.0

```

## MOB-af7b6bdfb07a

populated coordinator en 1024.0

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
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:139:9)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  populated coordinator en 1024.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated coordinator en 1024.0

```

## MOB-852f6c68ccb0

populated approver ar 320.0

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
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:139:9)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  populated approver ar 320.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated approver ar 320.0

```

## MOB-431eb41446be

populated approver en 1024.0

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
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_populated_layout_test.dart:139:9)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  populated approver en 1024.0
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: populated approver en 1024.0

```
