import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_intro_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_pending_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/widgets/kyc/kyc_status_summary_card.dart';

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

  testWidgets('does not fabricate KYC timing when the API has no values', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(384, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      _buildScreen(const KycPendingScreen(fullName: 'Backend User')),
    );
    await tester.pumpAndSettle();

    expect(find.text('Backend User'), findsOneWidget);
    expect(find.text('النهارده 9:41 ص'), findsNothing);
    expect(find.text('خلال 24 ساعة'), findsNothing);
    expect(
      tester
          .widget<KycStatusSummaryCard>(find.byType(KycStatusSummaryCard))
          .rows,
      hasLength(1),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows KYC timing only when supplied by the backend', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(384, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      _buildScreen(
        const KycPendingScreen(
          fullName: 'Backend User',
          submittedAt: '18 Sep 2026, 09:41',
          expectedReviewTime: '20 Sep 2026',
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('18 Sep 2026, 09:41'), findsOneWidget);
    expect(find.text('20 Sep 2026'), findsOneWidget);
    expect(
      tester
          .widget<KycStatusSummaryCard>(find.byType(KycStatusSummaryCard))
          .rows,
      hasLength(3),
    );
    expect(tester.takeException(), isNull);
  });
}

Widget _buildScreen(Widget child) {
  return EasyLocalization(
    supportedLocales: Languages.supportedLocales,
    path: Languages.translationsPath,
    startLocale: Languages.arabic.locale,
    fallbackLocale: Languages.arabic.locale,
    child: ScreenUtilInit(
      designSize: Size(ScreenSizes.width, ScreenSizes.height),
      builder: (context, _) => MaterialApp(home: child),
    ),
  );
}
