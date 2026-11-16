# company_rental_value_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_rental_value_test.dart
```

## MOB-bda1dc41d315

late report after account switch cannot restore private data

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
TimeoutException after 0:00:30.000000: Test timed out after 30 seconds. See https://pub.dev/packages/test#timeouts
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-a8786a9f9d33

CSV preview checks staff authority for the selected company

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_rental_value_test.dart 297:5           main.<fn>

```

## MOB-f24af84cb741

changing offer filters owns a fresh pager and closing disposes it once

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
Pending timers:
Timer (duration: 0:00:04.000000, periodic: false), created:
#0      new FakeTimer._ (package:fake_async/fake_async.dart:342:62)
#1      FakeAsync._createTimer (package:fake_async/fake_async.dart:260:29)
#2      FakeAsync.run.<anonymous closure> (package:fake_async/fake_async.dart:185:15)
#4      PausableTimer._startTimer (package:pausable_timer/pausable_timer.dart:78:22)
#5      PausableTimer.start (package:pausable_timer/pausable_timer.dart:193:5)
#6      new ToastificationItem (package:toastification/src/core/toastification_item.dart:74:10)
#7      ToastificationManager.showCustom (package:toastification/src/core/toastification_manager.dart:54:18)
#8      Toastification.showCustom (package:toastification/src/core/toastification.dart:163:20)
#9      Toastification.show (package:toastification/src/core/toastification.dart:283:12)
#10     Messages.showToast (package:melos_core/core/widgets/toast_messages/toast_message.dart:80:30)
#11     Messages.showReadError (package:melos_core/core/widgets/toast_messages/toast_message.dart:23:12)
#12     _PagifyErrorMapping._onError (package:melos_core/core/widgets/pagify_error_mapping.dart:73:14)
#13     _PagifyErrorMapping._onError.<anonymous closure> (package:melos_core/core/widgets/pagify_error_mapping.dart:46:3)
#14     _PagifyState._errorHandler (package:pagify/pagify.dart:480:27)
#15     _PagifyState._fetchPage.request (package:pagify/pagify.dart:602:15)
<asynchronous suspension>
(elided one frame from dart:async)

══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
A Timer is still pending even after the widget tree was disposed.
'package:flutter_test/src/binding.dart':
Failed assertion: line 2543 pos 12: '!timersPending'

When the exception was thrown, this was the stack:
#2      AutomatedTestWidgetsFlutterBinding._verifyInvariants (package:flutter_test/src/binding.dart:2543:12)
#3      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1974:7)
<asynchronous suspension>
<asynchronous suspension>
(elided 3 frames from class _AssertionError and package:stack_trace)

The test description was:
  changing offer filters owns a fresh pager and closing disposes it once
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: changing offer filters owns a fresh pager and closing disposes it once

```

## MOB-995baeacac71

three steps preserve exact money and never submit before final review

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
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "CompanyRequestPeople": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_rental_value_test.dart:402:7)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_rental_value_test.dart line 402
The test description was:
  three steps preserve exact money and never submit before final review
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: three steps preserve exact money and never submit before final review

```
