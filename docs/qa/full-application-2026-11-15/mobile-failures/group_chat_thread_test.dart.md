# group_chat_thread_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/group_chat_thread_test.dart
```

## MOB-7b06d9874d2c

opening a personal unread reminder clears it without rewinding receipts

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: [1]
  Actual: []
   Which: at location [0] is [] which shorter than expected

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 74:7               main.<fn>

```

## MOB-27124177c4df

opens without marking unread history as read or sending

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                               _Array.single
test/group_chat_thread_test.dart 88:57  main.<fn>

```

## MOB-f7982eb48731

Pagify inserts two local bubbles before ACK and replaces each identity once

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                               List.single
test/group_chat_thread_test.dart 98:45  main.<fn>

```

## MOB-7d7515f13373

offline local bubble retains its identity through socket retry

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                List.single
test/group_chat_thread_test.dart 162:54  main.<fn>

```

## MOB-7918aec13f47

reconnect drains never-sent queued messages in order and clears notice

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: an object with length of <2>
  Actual: []
   Which: has length of <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 196:7              main.<fn>

```

## MOB-dafd66f4ee63

reconnect never replays an unknown send or a rejected message

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: an object with length of <2>
  Actual: []
   Which: has length of <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 238:7              main.<fn>

```

## MOB-b5a3f409c095

reconnect revalidates removed send authority before draining

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 257:7              main.<fn>

```

## MOB-63e71bee1805

catch-up retains a message received during the initial history request

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 279:59  main.<fn>

```

## MOB-c8648f68611c

a read socket acknowledgement and its echo invalidate unread once

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: [1]
  Actual: []
   Which: at location [0] is [] which shorter than expected

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 293:9              main.<fn>

```

## MOB-0d0825f7f50b

presented messages share one read request and retain newer progress

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: [1]
  Actual: []
   Which: at location [0] is [] which shorter than expected

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 331:7              main.<fn>

```

## MOB-08db84dba3d4

other readers reload history only for affected outgoing messages

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 352:7              main.<fn>

```

## MOB-e79725c06a25

group read received before the send ACK is reconciled after insertion

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 394:48  main.<fn>

```

## MOB-385f3591b0c5

read receipt updates wait until the chat is visible again

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 442:5              main.<fn>

```

## MOB-59831513d075

failed receipt refresh waits for catch-up instead of rapid retry

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <2>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 462:7              main.<fn>

```

## MOB-d045d3b4dcc0

event recovery polling runs only while visible and disconnected

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: <1>
  Actual: <0>

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/group_chat_thread_test.dart:483:9)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1953:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/group_chat_thread_test.dart line 483
The test description was:
  event recovery polling runs only while visible and disconnected
════════════════════════════════════════════════════════════════════════════════════════════════════
Test failed. See exception logs above.
The test description was: event recovery polling runs only while visible and disconnected

```

## MOB-669cd5eb1e29

repeated connected notifications do not repeat event catch-up

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: <1>
  Actual: <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 510:7              main.<fn>

```

## MOB-4a8717d455bb

overlapping recovery checks share one message lookup

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 518:46  main.<fn>

```

## MOB-d40b44b34396

failed durable intent write blocks transmission and preserves composer

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 549:7              main.<fn>

```

## MOB-04fab1b2e0fa

intent and emptied composer persist before transport; double tap sends once

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: an object with length of <1>
  Actual: []
   Which: has length of <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 567:7              main.<fn>

```

## MOB-c9fe56c7344e

unknown outcome is looked up without resend and 404 stays unknown

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 591:44  main.<fn>

```

## MOB-42f2447789cb

explicit supported retry reuses exact operation; background lookup never sends

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-dd5fb7364881

supported retry reconciles a lost acknowledgement without another transmission

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-d320cad7f8d5

retry lookup outage preserves uncertainty and never transmits

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-14fedb06f43c

retry rechecks authority and refuses a replacement membership period

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-5ed94648eae2

revoked access while checking delivery cannot reissue the message

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-2e94dd134f2d

concurrent explicit retry taps issue one original operation

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-e103cb444b1c

account switch while lookup is pending blocks later retry transmission

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 627:38  main.unknownIntent

```

## MOB-2f062fc04d60

socket ack requires sender, conversation and client identity

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                _Array.single
test/group_chat_thread_test.dart 737:44  main.<fn>

```

## MOB-5cc3e2ac3ad3

duplicate events do not duplicate messages or resurrect deletion

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: an object with length of <1>
  Actual: []
   Which: has length of <0>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 770:7              main.<fn>

```

## MOB-8045add1f967

read cursor only advances for presented messages while visible

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: [1]
  Actual: []
   Which: at location [0] is [] which shorter than expected

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/group_chat_thread_test.dart 796:7              main.<fn>

```

## MOB-9d034c3539a5

access revocation clears private state and ignores late REST success

Result: `error`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Bad state: No element
dart:core                                List.single
test/group_chat_thread_test.dart 811:28  main.<fn>

```
