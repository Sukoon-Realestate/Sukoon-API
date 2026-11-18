# contextual_onboarding_widgets_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/contextual_onboarding_widgets_test.dart
```

## MOB-69c3b44585bb

real authorized tenant_home guides only present current controls

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
#0      Iterable.first (dart:core/iterable.dart:663:7)
#1      _FirstFinderMixin.filter (package:flutter_test/src/finders.dart:1383:28)
#3      _HitTestableWidgetFinder.filter (package:flutter_test/src/finders.dart:1479:29)
#5      Iterable.length (dart:core/iterable.dart:544:15)
#6      _FindsCountMatcher.describeMismatch (package:flutter_test/src/matchers.dart:1379:36)
#7      _expect.<anonymous closure> (package:matcher/src/expect/expect.dart:105:13)
#8      _expect (package:matcher/src/expect/expect.dart:182:17)
#9      expect (package:matcher/src/expect/expect.dart:65:3)
#10     expect (package:flutter_test/src/widget_tester.dart:473:18)
#11     main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/contextual_onboarding_widgets_test.dart:407:9)
<asynchronous suspension>
#12     testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#13     TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 3 frames from dart:async-patch and package:stack_trace)

The test description was:
  real authorized tenant_home guides only present current controls
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: real authorized tenant_home guides only present current controls

```
