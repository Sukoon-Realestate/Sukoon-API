import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/imports.dart';
import 'package:sokoun_app/shared_widgets/property_details_screen.dart';

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
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen() {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _PropertyDetailsAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: const PropertyDetailsScreen(),
          );
        },
      ),
    );
  }

  testWidgets('composes details and handles local actions', (tester) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(buildScreen());
    await tester.pumpAndSettle();

    expect(find.byType(TenantPropertyDetailsBody), findsOneWidget);
    expect(find.byType(TenantPropertyDetailsContentView), findsOneWidget);
    expect(find.byIcon(Icons.bookmark_border_rounded), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(
      find.byKey(const ValueKey('tenant-property-details-bottom-save')),
    );
    await tester.pump();

    expect(find.byIcon(Icons.bookmark_rounded), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('tenant-property-details-share')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantPropertyShareSheet), findsOneWidget);
    expect(find.text('مشاركة العقار'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('tenant-property-details-cancel-share')),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantPropertyShareSheet), findsNothing);
    expect(tester.takeException(), isNull);
  });
}

class _PropertyDetailsAssetLoader extends AssetLoader {
  const _PropertyDetailsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'cancel': 'إلغاء',
      'verified': 'موثّق',
      'tenant_visit_book_title': 'احجز زيارة',
      'tenant_property_details_share_title': 'مشاركة العقار',
      'tenant_property_details_copy_link': 'نسخ الرابط',
      'tenant_property_details_link_copied': 'تم نسخ الرابط',
      'tenant_property_details_share': 'مشاركة',
      'tenant_property_details_description': 'الوصف',
      'tenant_property_details_amenities': 'المرافق',
      'tenant_property_details_ownership_verified':
          'تم التحقق من إثبات الملكية',
      'tenant_property_details_phone_privacy':
          'رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة',
      'tenant_property_details_furnished': 'مفروشة',
      'tenant_property_details_monthly_price_unit': 'ج / شهر',
      'tenant_property_details_photo_count_unit': 'صورة',
      'tenant_property_details_photos': 'صور',
    };
  }
}
