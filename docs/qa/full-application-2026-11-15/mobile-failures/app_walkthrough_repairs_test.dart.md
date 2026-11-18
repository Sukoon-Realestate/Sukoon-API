# app_walkthrough_repairs_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/app_walkthrough_repairs_test.dart
```

## MOB-4511ee241386

unnamed chats retain a visible heading in list and conversation ar dark=false

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
Expected: exactly 2 matching candidates
  Actual: _TextWidgetFinder:<Found 1 widget with text "محادثة": [
            Text("محادثة", inherit: true, color: Color(alpha: 1.0000, red: 0.0471, green: 0.1647,
blue: 0.0941, colorSpace: ColorSpace.sRGB), family: SokounPlex, familyFallback: [], size: 14.0,
weight: 700, height: 1.4x, textAlign: start, overflow: ellipsis, maxLines: 1, dependencies:
[DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart:117:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart line 117
The test description was:
  unnamed chats retain a visible heading in list and conversation ar dark=false
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: unnamed chats retain a visible heading in list and conversation ar dark=false

```

## MOB-1be8e2fb974a

unnamed chats retain a visible heading in list and conversation en dark=false

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
Expected: exactly 2 matching candidates
  Actual: _TextWidgetFinder:<Found 1 widget with text "Conversation": [
            Text("Conversation", inherit: true, color: Color(alpha: 1.0000, red: 0.0471, green:
0.1647, blue: 0.0941, colorSpace: ColorSpace.sRGB), family: SokounPlex, familyFallback: [], size:
14.0, weight: 700, height: 1.4x, textAlign: start, overflow: ellipsis, maxLines: 1, dependencies:
[DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart:117:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart line 117
The test description was:
  unnamed chats retain a visible heading in list and conversation en dark=false
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: unnamed chats retain a visible heading in list and conversation en dark=false

```

## MOB-6fb0c864d1a1

unnamed chats retain a visible heading in list and conversation ar dark=true

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
Expected: exactly 2 matching candidates
  Actual: _TextWidgetFinder:<Found 1 widget with text "محادثة": [
            Text("محادثة", inherit: true, color: Color(alpha: 1.0000, red: 0.9255, green: 0.9490,
blue: 0.9176, colorSpace: ColorSpace.sRGB), family: SokounPlex, familyFallback: [], size: 14.0,
weight: 700, height: 1.4x, textAlign: start, overflow: ellipsis, maxLines: 1, dependencies:
[DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart:117:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart line 117
The test description was:
  unnamed chats retain a visible heading in list and conversation ar dark=true
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: unnamed chats retain a visible heading in list and conversation ar dark=true

```

## MOB-f3bf5920634a

unnamed chats retain a visible heading in list and conversation en dark=true

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
Expected: exactly 2 matching candidates
  Actual: _TextWidgetFinder:<Found 1 widget with text "Conversation": [
            Text("Conversation", inherit: true, color: Color(alpha: 1.0000, red: 0.9255, green:
0.9490, blue: 0.9176, colorSpace: ColorSpace.sRGB), family: SokounPlex, familyFallback: [], size:
14.0, weight: 700, height: 1.4x, textAlign: start, overflow: ellipsis, maxLines: 1, dependencies:
[DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is not enough

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart:117:11)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/app_walkthrough_repairs_test.dart line 117
The test description was:
  unnamed chats retain a visible heading in list and conversation en dark=true
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: unnamed chats retain a visible heading in list and conversation en dark=true

```
