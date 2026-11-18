# owner_banner_ads_flow_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/owner_banner_ads_flow_test.dart
```

## MOB-70cfbee6e15d

an existing pending ad is prepared for invoice review without charging

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
The following TestFailure was thrown while running async test code:
Expected: 'pending_payment'
  Actual: <null>
   Which: not an <Instance of 'String'>

When the exception was thrown, this was the stack:
#0      fail (package:matcher/src/expect/expect.dart:187:31)
#1      _expect (package:matcher/src/expect/expect.dart:182:3)
#2      expect (package:matcher/src/expect/expect.dart:65:3)
#3      expect (package:flutter_test/src/widget_tester.dart:473:18)
#4      main.<anonymous closure>.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:214:9)
<asynchronous suspension>
<asynchronous suspension>
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:207:7)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async and package:stack_trace)

The exception was caught asynchronously.
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: an existing pending ad is prepared for invoice review without charging

```

## MOB-472e397bc045

cached banner details cannot authorize or confirm a payment

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
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:241:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart line 241
The test description was:
  cached banner details cannot authorize or confirm a payment
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: cached banner details cannot authorize or confirm a payment

```

## MOB-c9797bb221a2

durable upload/create stops at invoice review without activating

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
The following TestFailure was thrown while running async test code:
Expected: 'pending_payment'
  Actual: <null>
   Which: not an <Instance of 'String'>

When the exception was thrown, this was the stack:
#0      fail (package:matcher/src/expect/expect.dart:187:31)
#1      _expect (package:matcher/src/expect/expect.dart:182:3)
#2      expect (package:matcher/src/expect/expect.dart:65:3)
#3      expect (package:flutter_test/src/widget_tester.dart:473:18)
#4      main.<anonymous closure>.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:335:9)
<asynchronous suspension>
<asynchronous suspension>
#6      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:323:7)
<asynchronous suspension>
#7      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#8      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async and package:stack_trace)

The exception was caught asynchronously.
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: durable upload/create stops at invoice review without activating

```

## MOB-caf9169eea1c

concurrent submission creates once and never charges

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
TimeoutException after 0:10:00.000000: Test timed out after 10 minutes.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-987e1ab7f392

lost create response reconciles after reopening without another upload

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
Reentrant call to runAsync() denied.
runAsync() was called, then before its future completed, it was called again. You must wait for the
first returned future to complete before calling runAsync() again.

When the exception was thrown, this was the stack:
#0      fail (package:matcher/src/expect/expect.dart:187:31)
#1      AutomatedTestWidgetsFlutterBinding.runAsync.<anonymous closure> (package:flutter_test/src/binding.dart:2274:7)
#2      AutomatedTestWidgetsFlutterBinding.runAsync (package:flutter_test/src/binding.dart:2280:6)
#3      WidgetTester.runAsync (package:flutter_test/src/widget_tester.dart:838:17)
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/owner_banner_ads_flow_test.dart:408:20)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  lost create response reconciles after reopening without another upload
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: lost create response reconciles after reopening without another upload

```
