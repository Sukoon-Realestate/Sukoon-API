import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/home_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/widgets/shared/home_bottom_navigation.dart';
import 'package:sokoun_app/features/notifications/presentation/screens/notifications_screen.dart';

import 'helpers/home_page_test_dependencies.dart';

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
    registerHomePageTestDependencies();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _HomeNavigationAssetLoader(),
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
            home: screen,
          );
        },
      ),
    );
  }

  testWidgets('keeps one navigation bar while switching tenant screens', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      buildScreen(const HomeScreen(userType: UserType.tenant)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(HomeBottomNavigation), findsOneWidget);
    expect(find.byType(TenantHomeScreen), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('home-navigation-1')));
    await tester.pumpAndSettle();

    expect(find.byType(HomeBottomNavigation), findsOneWidget);
    expect(find.byType(FavoritesScreen), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('home-navigation-0')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('tenant-open-notifications')));
    await tester.pumpAndSettle();

    expect(find.byType(HomeBottomNavigation), findsOneWidget);
    expect(find.byType(NotificationsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('uses the same navigation bar for owner destinations', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      buildScreen(const HomeScreen(userType: UserType.owner)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(HomeBottomNavigation), findsOneWidget);
    expect(find.byType(OwnerHomeScreen), findsOneWidget);
    expect(find.byKey(const ValueKey('home-navigation-4')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _HomeNavigationAssetLoader extends AssetLoader {
  const _HomeNavigationAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'home': 'الرئيسية',
      'favorites_navigation_saved': 'المحفوظات',
      'chats': 'الشات',
      'notifications': 'الإشعارات',
      'notifications_owner_properties_navigation': 'عقاراتي',
      'notifications_owner_requests_navigation': 'الطلبات',
      'notifications_owner_more_navigation': 'المزيد',
      'notifications_flow_title': 'الإشعارات',
      'notifications_mark_all_read': 'تحديد الكل كمقروء',
      'notification_settings_title': 'إعدادات الإشعارات',
      'favorites_title': 'المحفوظات',
      'favorites_saved_properties_count': 'عقارات محفوظة',
      'favorites_select_all': 'تحديد الكل',
      'favorites_currency_short': 'ج',
      'favorite_remove_semantic_label': 'إزالة من المحفوظات',
      'tenant_visit_banner_title': 'عندك زيارة النهارده 3:00 م',
      'tenant_visit_banner_property': 'شقة مدينة نصر',
    };
  }
}
