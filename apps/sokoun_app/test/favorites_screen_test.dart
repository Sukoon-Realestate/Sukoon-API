import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_property_card.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorites_empty_state.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/empty_results_state.dart';

import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, (call) async {
          return call.method == 'check' ? <String>['wifi'] : null;
        });
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
  });

  setUp(() async {
    await injector.reset();
    registerHomePageTestDependencies();
  });

  tearDown(() => injector.reset());

  Widget buildScreen({Widget screen = const FavoritesScreen()}) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _FavoritesTestAssetLoader(),
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

  testWidgets('lays out favorites and exposes the empty state after removal', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    final item = FavoritesContent.initialItems.first;

    await tester.pumpWidget(
      buildScreen(screen: FavoritesScreen(initialItems: [item])),
    );
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.byType(FavoritesScreen), findsOneWidget);
    expect(find.byType(FavoritePropertyCard), findsOneWidget);
    expect(find.bySemanticsLabel('تصفية'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.bySemanticsLabel('إزالة من المحفوظات'));
    await tester.pumpAndSettle();

    expect(find.byType(FavoritesEmptyState), findsOneWidget);
    expect(find.byType(FavoritePropertyCard), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('empty-state recovery actions navigate or update parent state', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      buildScreen(screen: const Scaffold(body: FavoritesEmptyState())),
    );
    await tester.pump();
    await tester.tap(find.text('تصفّح العقارات'));
    expect(Go.navigatorKey.currentState?.canPop(), isTrue);
    Go.back();
    await tester.pumpAndSettle();

    bool resetSearch = false;
    await tester.pumpWidget(
      buildScreen(
        screen: Scaffold(
          body: EmptyResultsState(
            onResetSearchPressed: () => resetSearch = true,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.tap(find.text('إعادة ضبط البحث والفلاتر'));
    expect(resetSearch, isTrue);
  });
}

class _FavoritesTestAssetLoader extends AssetLoader {
  const _FavoritesTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'favorites_title': 'المحفوظات',
      'favorites_saved_properties_count': 'عقارات محفوظة',
      'favorites_select_all': 'تحديد الكل',
      'home': 'الرئيسية',
      'favorites_navigation_saved': 'المحفوظات',
      'chats': 'الشات',
      'notifications': 'الإشعارات',
      'favorites_navigation_account': 'الحساب',
      'favorites_currency_short': 'ج',
      'favorite_remove_semantic_label': 'إزالة من المحفوظات',
      'favorites_removed_message': 'تمت إزالة العقار من المحفوظات',
      'favorites_undo_action': 'تراجع',
      'favorites_empty_title': 'لسه ما حفظتش عقارات',
      'favorites_empty_description':
          'اضغط على علامة القلب في أي عقار علشان تلاقيه هنا بعدين',
      'favorites_browse_properties': 'تصفّح العقارات',
      'filter': 'تصفية',
      'tenant_search_results_empty_title': 'لا توجد نتائج مطابقة',
      'tenant_search_results_empty_description':
          'جرّب تغيير البحث أو إزالة بعض الفلاتر',
      'tenant_search_results_reset_search': 'إعادة ضبط البحث والفلاتر',
    };
  }
}
