# housing_group_create_form_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/housing_group_create_form_test.dart
```

## MOB-3f6c1344524b

create group points to invalid city without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#226e5] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid city without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid city without the footer message

```

## MOB-c2447fcb404a

create group points to invalid scope without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#b3351] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid scope without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid scope without the footer message

```

## MOB-07b8a0ae31ff

create group points to invalid minimum budget without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#93d50] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid minimum budget without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid minimum budget without the footer message

```

## MOB-89767a26b0ae

create group points to invalid budget range without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#48747] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid budget range without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid budget range without the footer message

```

## MOB-c6c890a48422

create group points to invalid period without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#bdcf6] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid period without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid period without the footer message

```

## MOB-a7404c79852d

create group points to invalid start date without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#272cf] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid start date without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid start date without the footer message

```

## MOB-61ca418d045e

create group points to invalid end date without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#20f7c] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid end date without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid end date without the footer message

```

## MOB-abe608ce9dc6

create group points to invalid occupants without the footer message

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
  Actual: _HitTestableWidgetFinder:<Found 0 widgets with key [GlobalKey#bcf6b] (considering only
hit-testable widgets with a RenderBox): []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:227:9)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 227
The test description was:
  create group points to invalid occupants without the footer message
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: create group points to invalid occupants without the footer message

```

## MOB-046e21c43742

Arabic group form advances to the next invalid field

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
Expected: true
  Actual: <false>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:239:7)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 239
The test description was:
  Arabic group form advances to the next invalid field
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: Arabic group form advances to the next invalid field

```

## MOB-2ec2f4b0e33a

calendar dates and Arabic numbers reach a single group creation request

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
[🌎 Easy Localization] [DEBUG] Load Localization Delegate
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "PremiumConfirmSheet": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:323:7)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 323
The test description was:
  calendar dates and Arabic numbers reach a single group creation request
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: calendar dates and Arabic numbers reach a single group creation request

```

## MOB-5d50da117211

restored group fields keep dates and ordered validation

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
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "PremiumConfirmSheet": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart:402:7)
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
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_group_create_form_test.dart line 402
The test description was:
  restored group fields keep dates and ordered validation
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: restored group fields keep dates and ordered validation

```
