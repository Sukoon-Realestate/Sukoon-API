# feature_tools_flows_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/feature_tools_flows_test.dart
```

## MOB-35e646ff7ff6

rent records remain reachable while the payment provider is disabled

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
  Actual: _TextWidgetFinder:<Found 2 widgets with text "دفع الإيجار الإلكتروني غير متاح حاليًا.
يمكنك مراجعة الفاتورة وحالة السداد.": [
            Text("دفع الإيجار الإلكتروني غير متاح حاليًا. يمكنك مراجعة الفاتورة وحالة السداد.",
inherit: true, family: SokounPlex, familyFallback: [], weight: 400, height: 1.6x, textAlign: start,
dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
            Text("دفع الإيجار الإلكتروني غير متاح حاليًا. يمكنك مراجعة الفاتورة وحالة السداد.",
inherit: true, family: SokounPlex, familyFallback: [], weight: 400, height: 1.6x, textAlign: start,
dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is too many

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/feature_tools_flows_test.dart:385:7)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/feature_tools_flows_test.dart line 385
The test description was:
  rent records remain reachable while the payment provider is disabled
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: rent records remain reachable while the payment provider is disabled

```

## MOB-92821bf9c111

a payable invoice keeps its payment action disabled with the provider reason

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
  Actual: _TextWidgetFinder:<Found 2 widgets with text "دفع الإيجار الإلكتروني غير متاح حاليًا.
يمكنك مراجعة الفاتورة وحالة السداد.": [
            Text("دفع الإيجار الإلكتروني غير متاح حاليًا. يمكنك مراجعة الفاتورة وحالة السداد.",
inherit: true, family: SokounPlex, familyFallback: [], weight: 400, height: 1.6x, textAlign: start,
dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
            Text("دفع الإيجار الإلكتروني غير متاح حاليًا. يمكنك مراجعة الفاتورة وحالة السداد.",
inherit: true, family: SokounPlex, familyFallback: [], weight: 400, height: 1.6x, textAlign: start,
dependencies: [DefaultSelectionStyle, DefaultTextStyle, MediaQuery]),
          ]>
   Which: is too many

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/feature_tools_flows_test.dart:408:7)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/feature_tools_flows_test.dart line 408
The test description was:
  a payable invoice keeps its payment action disabled with the provider reason
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: a payable invoice keeps its payment action disabled with the provider reason

```
