# screen_audit_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/screen_audit_test.dart
```

## MOB-dfa304187ab9

ChatForwardBatchScreen phone-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-3cdb9491c824

ChatForwardBatchScreen phone-en

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-b2aa6f24ef0d

ChatForwardBatchScreen se-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-03734340e3f0

ChatForwardBatchScreen se-en

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-b3ce2996936e

ChatForwardBatchScreen large-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-5e5db15189d0

ChatForwardBatchScreen dark-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-cd7ca2177d95

OwnerTourEditorScreen phone-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-30c0feee1e91

OwnerTourEditorScreen phone-en

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-58aee17945f2

OwnerTourEditorScreen se-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-15ea2d203798

OwnerTourEditorScreen se-en

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-b3d517e98825

OwnerTourEditorScreen large-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-73202ccc3646

OwnerTourEditorScreen dark-ar

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
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-61090f6cc6e0

SupportTicketDetailContentView phone-ar

Result: `error`.

```text
ndOnInheritedWidgetOfExactType (package:flutter/src/widgets/framework.dart:5095:12)
#3      LookupBoundary.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/lookup_boundary.dart:99:13)
#4      View.maybeOf (package:flutter/src/widgets/view.dart:137:27)
#5      _ScreenUtilInitState._newData (package:flutter_screenutil/src/screenutil_init.dart:138:23)
#6      _ScreenUtilInitState._revalidate (package:flutter_screenutil/src/screenutil_init.dart:164:21)
#7      _ScreenUtilInitState.didChangeMetrics (package:flutter_screenutil/src/screenutil_init.dart:128:5)
#8      WidgetsBinding.handleMetricsChanged (package:flutter/src/widgets/binding.dart:926:18)
#9      TestPlatformDispatcher._handleMetricsChanged (package:flutter_test/src/window.dart:215:24)
#10     TestFlutterView.resetPhysicalConstraints (package:flutter_test/src/window.dart:1162:42)
#11     TestFlutterView.resetPhysicalSize (package:flutter_test/src/window.dart:1137:5)
#12     TestFlutterView.reset (package:flutter_test/src/window.dart:1295:5)
#14     Invoker.runTearDowns.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:296:18)
#15     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#20     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#21     Invoker.runTearDowns.<anonymous closure> (package:test_api/src/backend/invoker.dart:295:9)
#26     Invoker.runTearDowns (package:test_api/src/backend/invoker.dart:290:12)
#27     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:459:23)
#28     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#33     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#34     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:458:21)
<asynchronous suspension>
(elided 13 frames from dart:async)
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY WIDGETS LIBRARY ╞═══════════════════════════════════════════════════════════
The following assertion was thrown while dispatching notifications for
WidgetsBindingObserver.didChangeMetrics:
Looking up a deactivated widget's ancestor is unsafe.
At this point the state of the widget's element tree is no longer stable.
To safely refer to a widget's ancestor in its dispose() method, save a reference to the ancestor by
calling dependOnInheritedWidgetOfExactType() in the widget's didChangeDependencies() method.

When the exception was thrown, this was the stack:
#0      Element._debugCheckStateIsActiveForAncestorLookup.<anonymous closure> (package:flutter/src/widgets/framework.dart:5062:9)
#1      Element._debugCheckStateIsActiveForAncestorLookup (package:flutter/src/widgets/framework.dart:5076:6)
#2      Element.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/framework.dart:5095:12)
#3      LookupBoundary.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/lookup_boundary.dart:99:13)
#4      View.maybeOf (package:flutter/src/widgets/view.dart:137:27)
#5      _ScreenUtilInitState._newData (package:flutter_screenutil/src/screenutil_init.dart:138:23)
#6      _ScreenUtilInitState._revalidate (package:flutter_screenutil/src/screenutil_init.dart:164:21)
#7      _ScreenUtilInitState.didChangeMetrics (package:flutter_screenutil/src/screenutil_init.dart:128:5)
#8      WidgetsBinding.handleMetricsChanged (package:flutter/src/widgets/binding.dart:926:18)
#9      TestPlatformDispatcher._handleMetricsChanged (package:flutter_test/src/window.dart:215:24)
#10     TestFlutterView.resetSystemGestureInsets (package:flutter_test/src/window.dart:1189:42)
#11     TestFlutterView.reset (package:flutter_test/src/window.dart:1297:5)
#13     Invoker.runTearDowns.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:296:18)
#14     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#19     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#20     Invoker.runTearDowns.<anonymous closure> (package:test_api/src/backend/invoker.dart:295:9)
#25     Invoker.runTearDowns (package:test_api/src/backend/invoker.dart:290:12)
#26     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:459:23)
#27     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#32     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#33     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:458:21)
<asynchronous suspension>
(elided 13 frames from dart:async)
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY WIDGETS LIBRARY ╞═══════════════════════════════════════════════════════════
The following assertion was thrown while dispatching notifications for
WidgetsBindingObserver.didChangeMetrics:
Looking up a deactivated widget's ancestor is unsafe.
At this point the state of the widget's element tree is no longer stable.
To safely refer to a widget's ancestor in its dispose() method, save a reference to the ancestor by
calling dependOnInheritedWidgetOfExactType() in the widget's didChangeDependencies() method.

When the exception was thrown, this was the stack:
#0      Element._debugCheckStateIsActiveForAncestorLookup.<anonymous closure> (package:flutter/src/widgets/framework.dart:5062:9)
#1      Element._debugCheckStateIsActiveForAncestorLookup (package:flutter/src/widgets/framework.dart:5076:6)
#2      Element.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/framework.dart:5095:12)
#3      LookupBoundary.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/lookup_boundary.dart:99:13)
#4      View.maybeOf (package:flutter/src/widgets/view.dart:137:27)
#5      _ScreenUtilInitState._newData (package:flutter_screenutil/src/screenutil_init.dart:138:23)
#6      _ScreenUtilInitState._revalidate (package:flutter_screenutil/src/screenutil_init.dart:164:21)
#7      _ScreenUtilInitState.didChangeMetrics (package:flutter_screenutil/src/screenutil_init.dart:128:5)
#8      WidgetsBinding.handleMetricsChanged (package:flutter/src/widgets/binding.dart:926:18)
#9      TestPlatformDispatcher._handleMetricsChanged (package:flutter_test/src/window.dart:215:24)
#10     TestFlutterView.resetViewInsets (package:flutter_test/src/window.dart:1215:42)
#11     TestFlutterView.reset (package:flutter_test/src/window.dart:1298:5)
#13     Invoker.runTearDowns.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:296:18)
#14     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#19     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#20     Invoker.runTearDowns.<anonymous closure> (package:test_api/src/backend/invoker.dart:295:9)
#25     Invoker.runTearDowns (package:test_api/src/backend/invoker.dart:290:12)
#26     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:459:23)
#27     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#32     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#33     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:458:21)
<asynchronous suspension>
(elided 13 frames from dart:async)
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY WIDGETS LIBRARY ╞═══════════════════════════════════════════════════════════
The following assertion was thrown while dispatching notifications for
WidgetsBindingObserver.didChangeMetrics:
Looking up a deactivated widget's ancestor is unsafe.
At this point the state of the widget's element tree is no longer stable.
To safely refer to a widget's ancestor in its dispose() method, save a reference to the ancestor by
calling dependOnInheritedWidgetOfExactType() in the widget's didChangeDependencies() method.

When the exception was thrown, this was the stack:
#0      Element._debugCheckStateIsActiveForAncestorLookup.<anonymous closure> (package:flutter/src/widgets/framework.dart:5062:9)
#1      Element._debugCheckStateIsActiveForAncestorLookup (package:flutter/src/widgets/framework.dart:5076:6)
#2      Element.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/framework.dart:5095:12)
#3      LookupBoundary.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/lookup_boundary.dart:99:13)
#4      View.maybeOf (package:flutter/src/widgets/view.dart:137:27)
#5      _ScreenUtilInitState._newData (package:flutter_screenutil/src/screenutil_init.dart:138:23)
#6      _ScreenUtilInitState._revalidate (package:flutter_screenutil/src/screenutil_init.dart:164:21)
#7      _ScreenUtilInitState.didChangeMetrics (package:flutter_screenutil/src/screenutil_init.dart:128:5)
#8      WidgetsBinding.handleMetricsChanged (package:flutter/src/widgets/binding.dart:926:18)
#9      TestPlatformDispatcher._handleMetricsChanged (package:flutter_test/src/window.dart:215:24)
#10     TestFlutterView.resetViewPadding (package:flutter_test/src/window.dart:1241:42)
#11     TestFlutterView.reset (package:flutter_test/src/window.dart:1299:5)
#13     Invoker.runTearDowns.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:296:18)
#14     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#19     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#20     Invoker.runTearDowns.<anonymous closure> (package:test_api/src/backend/invoker.dart:295:9)
#25     Invoker.runTearDowns (package:test_api/src/backend/invoker.dart:290:12)
#26     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:459:23)
#27     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#32     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#33     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:458:21)
<asynchronous suspension>
(elided 13 frames from dart:async)
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY WIDGETS LIBRARY ╞═══════════════════════════════════════════════════════════
The following assertion was thrown while dispatching notifications for
WidgetsBindingObserver.didChangeMetrics:
Looking up a deactivated widget's ancestor is unsafe.
At this point the state of the widget's element tree is no longer stable.
To safely refer to a widget's ancestor in its dispose() method, save a reference to the ancestor by
calling dependOnInheritedWidgetOfExactType() in the widget's didChangeDependencies() method.

When the exception was thrown, this was the stack:
#0      Element._debugCheckStateIsActiveForAncestorLookup.<anonymous closure> (package:flutter/src/widgets/framework.dart:5062:9)
#1      Element._debugCheckStateIsActiveForAncestorLookup (package:flutter/src/widgets/framework.dart:5076:6)
#2      Element.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/framework.dart:5095:12)
#3      LookupBoundary.dependOnInheritedWidgetOfExactType (package:flutter/src/widgets/lookup_boundary.dart:99:13)
#4      View.maybeOf (package:flutter/src/widgets/view.dart:137:27)
#5      _ScreenUtilInitState._newData (package:flutter_screenutil/src/screenutil_init.dart:138:23)
#6      _ScreenUtilInitState._revalidate (package:flutter_screenutil/src/screenutil_init.dart:164:21)
#7      _ScreenUtilInitState.didChangeMetrics (package:flutter_screenutil/src/screenutil_init.dart:128:5)
#8      WidgetsBinding.handleMetricsChanged (package:flutter/src/widgets/binding.dart:926:18)
#9      TestPlatformDispatcher._handleMetricsChanged (package:flutter_test/src/window.dart:215:24)
#10     TestFlutterView.resetGestureSettings (package:flutter_test/src/window.dart:1266:42)
#11     TestFlutterView.reset (package:flutter_test/src/window.dart:1300:5)
#13     Invoker.runTearDowns.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:296:18)
#14     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#19     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#20     Invoker.runTearDowns.<anonymous closure> (package:test_api/src/backend/invoker.dart:295:9)
#25     Invoker.runTearDowns (package:test_api/src/backend/invoker.dart:290:12)
#26     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:459:23)
#27     Invoker._waitForOutstandingCallbacks.<anonymous closure> (package:test_api/src/backend/invoker.dart:318:17)
#32     Invoker._waitForOutstandingCallbacks (package:test_api/src/backend/invoker.dart:314:5)
#33     Invoker._onRun.<anonymous closure>.<anonymous closure>.<anonymous closure> (package:test_api/src/backend/invoker.dart:458:21)
<asynchronous suspension>
(elided 13 frames from dart:async)
════════════════════════════════════════════════════════════════════════════════════════════════════
```

## MOB-cfae34305fce

SupportTicketDetailContentView phone-en

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded en
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-2d65d7421b37

SupportTicketDetailContentView se-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-66e9c2a928df

SupportTicketDetailContentView se-en

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded en
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-3480f2109cb3

SupportTicketDetailContentView large-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-6257ed6b5d1d

SupportTicketDetailContentView dark-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-163e62ef82e4

SupportHelpContentView phone-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-e99628de82bc

SupportHelpContentView phone-en

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded en
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-e194554769fa

SupportHelpContentView se-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-b8ce7b85ef78

SupportHelpContentView se-en

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded en
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-e65d58c3340a

SupportHelpContentView large-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```

## MOB-1cdea1a4a074

SupportHelpContentView dark-ar

Result: `error`.

```text
[🌎 Easy Localization] [DEBUG] Start
[🌎 Easy Localization] [DEBUG] Init state
[🌎 Easy Localization] [INFO] Start locale loaded ar
[🌎 Easy Localization] [DEBUG] Build
[🌎 Easy Localization] [DEBUG] Init Localization Delegate
[🌎 Easy Localization] [DEBUG] Init provider
'package:flutter_test/src/binding.dart': Failed assertion: line 1912 pos 9: '_pendingExceptionDetails != null': A test overrode FlutterError.onError but either failed to return it to its original state, or had unexpected additional errors that it could not handle. Typically, this is caused by using expect() before restoring FlutterError.onError.
dart:core                                           _AssertionError._throwNew
package:flutter_test/src/binding.dart 1912:9        TestWidgetsFlutterBinding._runTest.handleUncaughtError
package:flutter_test/src/binding.dart 1921:13       TestWidgetsFlutterBinding._runTest.<fn>
===== asynchronous gap ===========================
dart:async                                          _CustomZone.registerBinaryCallback
package:flutter_test/src/binding.dart 1942:5        TestWidgetsFlutterBinding._runTestBody
dart:async                                          _CustomZone.runBinary
package:flutter_test/src/binding.dart 1927:10       TestWidgetsFlutterBinding._runTest
package:flutter_test/src/binding.dart 2490:24       AutomatedTestWidgetsFlutterBinding.runTest.<fn>
package:fake_async/fake_async.dart 182:47           FakeAsync.run.<fn>.<fn>
dart:async                                          runZoned
package:clock/src/default.dart 52:10                withClock
package:fake_async/fake_async.dart 182:15           FakeAsync.run.<fn>
dart:async                                          runZoned
package:fake_async/fake_async.dart 181:52           FakeAsync.run
package:flutter_test/src/binding.dart 2487:15       AutomatedTestWidgetsFlutterBinding.runTest
package:flutter_test/src/widget_tester.dart 184:24  testWidgets.<fn>

TimeoutException after 0:00:45.000000: Test timed out after 45 seconds.
dart:isolate  _RawReceivePort._handleMessage

```
