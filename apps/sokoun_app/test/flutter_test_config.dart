import 'dart:async';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Mock protected device storage only for suites that initialize a widget binding.
/// Pure loopback HTTP suites retain their normal HttpClient and test real cookies.
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  final Map<String, String> records = {};
  final Directory directory = await Directory.systemTemp.createTemp(
    'sokoun-test-storage-',
  );
  setUp(records.clear);
  tearDownAll(() async {
    if (await directory.exists()) await directory.delete(recursive: true);
  });
  await testMain();
  try {
    TestWidgetsFlutterBinding.instance;
  } catch (_) {
    return;
  }
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  messenger.setMockMethodCallHandler(
    const MethodChannel('plugins.flutter.io/shared_preferences'),
    (call) async => call.method == 'getAll' ? <String, Object>{} : true,
  );
  messenger.setMockMethodCallHandler(
    const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
    (call) async {
      final Map arguments = call.arguments as Map? ?? const {};
      final String key = arguments['key']?.toString() ?? '';
      switch (call.method) {
        case 'read':
          return records[key];
        case 'readAll':
          return Map<String, String>.of(records);
        case 'write':
          records[key] = arguments['value'] as String;
          return null;
        case 'delete':
          records.remove(key);
          return null;
        case 'deleteAll':
          records.clear();
          return null;
        case 'containsKey':
          return records.containsKey(key);
      }
      return null;
    },
  );
  messenger.setMockMethodCallHandler(
    const MethodChannel('plugins.flutter.io/path_provider'),
    (_) async => directory.path,
  );
}
