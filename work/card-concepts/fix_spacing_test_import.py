from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/property_memory_badge_spacing_test.dart')
s=p.read_text().replace("import 'package:flutter_secure_storage/flutter_secure_storage.dart';", "import 'package:flutter/services.dart';")
s=s.replace('    FlutterSecureStorage.setMockInitialValues({});', '''    final disk = <String, String>{};
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (call) async {
            final key = call.arguments['key'] as String;
            if (call.method == 'write') {
              disk[key] = call.arguments['value'] as String;
              return null;
            }
            return disk[key];
          },
        );''')
p.write_text(s)
