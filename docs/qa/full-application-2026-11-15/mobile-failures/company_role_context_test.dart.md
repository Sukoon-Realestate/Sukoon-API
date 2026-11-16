# company_role_context_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_role_context_test.dart
```

## MOB-99274315f210

company discovery exposes no unscoped execution routes

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
Expected: no matching candidates
  Actual: _TypeWidgetFinder:<Found 1 widget with type "CompanyContractEntry": [
            CompanyContractEntry,
          ]>
   Which: means one was found but none were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_context_test.dart:84:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/company_role_context_test.dart line 84
The test description was:
  company discovery exposes no unscoped execution routes
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: company discovery exposes no unscoped execution routes

```

## MOB-c9c884e970b9

multiple roles require a choice and carry one transport role

Result: `failure`.

```text
Expected: CompanyRole:<CompanyRole.coordinator>
  Actual: <null>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_role_context_test.dart 109:7           main.<fn>

```

## MOB-e6e473b3081b

one role opens directly and revocation removes the old selection

Result: `failure`.

```text
Expected: CompanyRole:<CompanyRole.payer>
  Actual: <null>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_role_context_test.dart 126:7           main.<fn>

```

## MOB-43eb1a213f05

a remembered role is verified against current server roles

Result: `failure`.

```text
Expected: CompanyRole:<CompanyRole.coordinator>
  Actual: <null>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_role_context_test.dart 140:5           main.<fn>

```

## MOB-caca00291a30

a late company response cannot restore its role or data

Result: `failure`.

```text
Expected: 'b'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: b

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_role_context_test.dart 156:5           main.<fn>

```
