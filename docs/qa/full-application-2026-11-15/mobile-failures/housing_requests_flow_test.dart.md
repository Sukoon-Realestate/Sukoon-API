# housing_requests_flow_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/housing_requests_flow_test.dart
```

## MOB-0d442b2138d1

permissions are followed by the real published-request collection

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
#1      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_requests_flow_test.dart:61:14)
<asynchronous suspension>
#2      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#3      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  permissions are followed by the real published-request collection
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: permissions are followed by the real published-request collection

```

## MOB-6aa8a8e562e1

changing between own requests and owner demand reloads the right collection

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
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Published request": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_requests_flow_test.dart:79:7)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_requests_flow_test.dart line 79
The test description was:
  changing between own requests and owner demand reloads the right collection
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: changing between own requests and owner demand reloads the right collection

```

## MOB-aa46d6a28b55

missing pagination cannot silently turn a returned request into an empty list

Result: `failure`.

```text
Expected: throws <Instance of 'ServerException'>
  Actual: <Instance of 'Future<(List<HousingRequest>, PaginationData)>'>
   Which: threw ServerFailure:<ServerFailure(الخدمة عبر الإنترنت غير متاحة بعد, 403, null, null)>
          stack package:sokoun_app/features/shared/premium/data/planning_api_data.dart 74:7  PlanningApiData.page
                ===== asynchronous gap ===========================
                package:matcher                                                              expectLater
                package:flutter_test/src/widget_tester.dart 507:8                            expectLater
                test/housing_requests_flow_test.dart 97:13                                   main.<fn>
                
          which is not an instance of 'ServerException'

package:matcher                                    expectLater
package:flutter_test/src/widget_tester.dart 507:8  expectLater
test/housing_requests_flow_test.dart 97:13         main.<fn>

```
