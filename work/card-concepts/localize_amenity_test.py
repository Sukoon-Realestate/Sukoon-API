from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/property_amenity_row_test.dart')
s=p.read_text()
s="import 'dart:convert';\nimport 'dart:io';\nimport 'package:easy_localization/easy_localization.dart';\nimport 'package:flutter/services.dart';\n"+s
s=s.replace('void main() {', '''void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
  });''')
s=s.replace('ScreenUtilInit(', '''EasyLocalization(
        supportedLocales: [Locale(direction == TextDirection.rtl ? 'ar' : 'en')],
        path: 'unused',
        assetLoader: const _Translations(),
        startLocale: Locale(direction == TextDirection.rtl ? 'ar' : 'en'),
        child: ScreenUtilInit(''',1)
s=s.replace('builder: (context, child) => MaterialApp(', '''builder: (context, child) => MaterialApp(
              localizationsDelegates: context.localizationDelegates,
              supportedLocales: context.supportedLocales,
              locale: context.locale,''',1)
needle='''        ),
      );'''
assert needle in s
s=s.replace(needle,'''        ),
        ),
      );''',1)
s+='''
class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(File('../../packages/core/assets/translations/${locale.languageCode}.json').readAsStringSync()) as Map<String, dynamic>;
}
'''
p.write_text(s)
