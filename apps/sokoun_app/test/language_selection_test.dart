import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui show TextDirection;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const MethodChannel preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await CacheStorage.init();
  });

  setUp(() async {
    await CacheStorage.write('locale', 'ar');
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
  });

  Future<void> openPicker(WidgetTester tester) async {
    await tester.tap(find.text('Open language'));
    await tester.pumpAndSettle();
    expect(find.byType(LanguageSelectionScreen), findsOneWidget);
  }

  void configureViewport(WidgetTester tester, Size size) {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  testWidgets('confirms and persists either locale and restores selection', (
    tester,
  ) async {
    configureViewport(tester, const Size(390, 844));
    await tester.pumpWidget(_buildApp());
    await tester.pumpAndSettle();
    await openPicker(tester);

    expect(find.text('اختر اللغة'), findsOneWidget);
    expect(find.text('Choose your preferred language'), findsOneWidget);
    expect(find.text('العربية'), findsOneWidget);
    expect(find.text('الإنجليزية'), findsOneWidget);
    await tester.tap(find.text('English'));
    await tester.pump();

    expect(Go.context.locale, const Locale('ar'));
    expect(CacheStorage.read('locale'), 'ar');
    await tester.tap(find.text('تأكيد'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsNothing);
    expect(Go.context.locale, const Locale('en'));
    expect(
      Directionality.of(tester.element(find.text('Open language'))),
      ui.TextDirection.ltr,
    );
    expect(CacheStorage.read('locale'), 'en');

    await openPicker(tester);
    final LanguageOptionCard english = tester.widget<LanguageOptionCard>(
      find.widgetWithText(LanguageOptionCard, 'English'),
    );
    expect(english.selected, isTrue);
    await tester.tap(find.text('Arabic'));
    await tester.pump();
    await tester.tap(find.text('Confirm'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsNothing);
    expect(Go.context.locale, const Locale('ar'));
    expect(
      Directionality.of(tester.element(find.text('Open language'))),
      ui.TextDirection.rtl,
    );
    expect(CacheStorage.read('locale'), 'ar');
    expect(tester.takeException(), isNull);
  });

  testWidgets('back discards the draft and unchanged confirmation returns', (
    tester,
  ) async {
    configureViewport(tester, const Size(390, 844));
    await tester.pumpWidget(_buildApp());
    await tester.pumpAndSettle();
    await openPicker(tester);
    await tester.tap(find.text('English'));
    await tester.pump();
    await tester.tap(
      find.byTooltip(
        MaterialLocalizations.of(
          tester.element(find.byType(LanguageSelectionScreen)),
        ).backButtonTooltip,
      ),
    );
    await tester.pumpAndSettle();

    expect(Go.context.locale, const Locale('ar'));
    expect(CacheStorage.read('locale'), 'ar');
    await openPicker(tester);
    final LanguageOptionCard arabic = tester.widget<LanguageOptionCard>(
      find.widgetWithText(LanguageOptionCard, 'العربية'),
    );
    expect(arabic.selected, isTrue);
    await tester.tap(find.text('تأكيد'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsNothing);
    expect(CacheStorage.read('locale'), 'ar');
    expect(tester.takeException(), isNull);
  });

  testWidgets('small screens with enlarged text keep confirmation reachable', (
    tester,
  ) async {
    configureViewport(tester, const Size(320, 568));
    await tester.pumpWidget(_buildApp(textScale: 2));
    await tester.pumpAndSettle();
    await openPicker(tester);

    await tester.ensureVisible(find.text('تأكيد'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تأكيد'));
    await tester.pumpAndSettle();

    expect(find.byType(LanguageSelectionScreen), findsNothing);
    expect(tester.takeException(), isNull);
  });
}

Widget _buildApp({double textScale = 1}) {
  return EasyLocalization(
    supportedLocales: Languages.supportedLocales,
    path: Languages.translationsPath,
    assetLoader: const _TranslationsAssetLoader(),
    startLocale: Languages.arabic.locale,
    fallbackLocale: Languages.arabic.locale,
    child: ScreenUtilInit(
      designSize: Size(ScreenSizes.width, ScreenSizes.height),
      builder: (context, _) => MaterialApp(
        navigatorKey: Go.navigatorKey,
        localizationsDelegates: context.localizationDelegates,
        supportedLocales: context.supportedLocales,
        locale: context.locale,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: Scaffold(
          body: Center(
            child: TextButton(
              onPressed: () => Go.to(const LanguageSelectionScreen()),
              child: const Text('Open language'),
            ),
          ),
        ),
      ),
    ),
  );
}

class _TranslationsAssetLoader extends AssetLoader {
  const _TranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    final String relativePath =
        'packages/core/assets/translations/${locale.languageCode}.json';
    final File file = File(relativePath).existsSync()
        ? File(relativePath)
        : File('../../$relativePath');
    return jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  }
}
