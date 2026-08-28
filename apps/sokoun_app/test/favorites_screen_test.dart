import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_property_card.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorites_empty_state.dart';

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

  Widget buildScreen({FavoritesScreen screen = const FavoritesScreen()}) {
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
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(ValueKey('favorite-remove-${item.id}')));
    await tester.pumpAndSettle();

    expect(find.byType(FavoritesEmptyState), findsOneWidget);
    expect(find.byType(FavoritePropertyCard), findsNothing);
    expect(tester.takeException(), isNull);
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
    };
  }
}
