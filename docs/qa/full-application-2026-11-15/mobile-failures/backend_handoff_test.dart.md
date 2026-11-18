# backend_handoff_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/backend_handoff_test.dart
```

## MOB-92d054aee569

video and canonical property links survive cache round trips

Result: `failure`.

```text
Expected: 'https://sokoun.app/properties/property-2'
  Actual: 'https://sukoon.rent/properties/property-2'
   Which: is different.
          Expected: https://sokoun.app/ ...
            Actual: https://sukoon.rent ...
                             ^
           Differ at offset 9

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/backend_handoff_test.dart 122:5                main.<fn>

```

## MOB-bed369029d14

partial KYC stays on form and successful completion keeps the signed-in journey

Result: `error`.

```text
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
The finder "Found 0 widgets with text "Next review data": []" (used in a call to "tap()") could not
find any matching widgets.

When the exception was thrown, this was the stack:
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2095:7)
#1      WidgetController.getCenter (package:flutter_test/src/controller.dart:1947:12)
#2      WidgetController.tap (package:flutter_test/src/controller.dart:1080:7)
#3      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/backend_handoff_test.dart:345:20)
<asynchronous suspension>
#4      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#5      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  partial KYC stays on form and successful completion keeps the signed-in journey
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: partial KYC stays on form and successful completion keeps the signed-in journey

```
