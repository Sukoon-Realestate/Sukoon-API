import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_intro_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  testWidgets('lays out the KYC upload screen at a compact phone size', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(384, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: Languages.supportedLocales,
        path: Languages.translationsPath,
        startLocale: Languages.arabic.locale,
        fallbackLocale: Languages.arabic.locale,
        child: ScreenUtilInit(
          designSize: Size(ScreenSizes.width, ScreenSizes.height),
          builder: (context, _) {
            return const MaterialApp(home: KycUploadDocumentsScreen());
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(KycUploadDocumentsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('lays out the KYC intro with its internal scroll view', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(384, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: Languages.supportedLocales,
        path: Languages.translationsPath,
        startLocale: Languages.arabic.locale,
        fallbackLocale: Languages.arabic.locale,
        child: ScreenUtilInit(
          designSize: Size(ScreenSizes.width, ScreenSizes.height),
          builder: (context, _) {
            return const MaterialApp(home: KycIntroScreen());
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(KycIntroScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
