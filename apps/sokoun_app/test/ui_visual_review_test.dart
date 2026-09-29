import 'dart:io';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_stats_grid.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_property_card.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

/// Opt-in PNG export; the same fixtures are used before and after refinement.
/// flutter test test/ui_visual_review_test.dart --dart-define=UI_REVIEW_DIR=/tmp/review
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const String output = String.fromEnvironment('UI_REVIEW_DIR');
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    final FontLoader fonts = FontLoader(ConstantManager.fontFamily);
    for (final String weight in [
      'Regular',
      'Medium',
      'Bold',
      'ExtraBold',
      'Black',
    ]) {
      fonts.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await fonts.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });

  for (final String locale in ['ar', 'en']) {
    for (final double width in [390.0, 1024.0]) {
      for (final String subject in ['welcome', 'discovery', 'dashboard']) {
        testWidgets('$subject $locale at $width', (tester) async {
          tester.view.physicalSize = Size(width, width > 600 ? 768 : 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          final Widget screen = switch (subject) {
            'welcome' => const WelcomeScreen(),
            'dashboard' => AppScaffold(
              showBackButton: false,
              contentWidth: SokounContentWidth.wide,
              body: const SingleChildScrollView(
                padding: EdgeInsets.all(20),
                child: OwnerStatsGrid(
                  visitsThisWeek: 12,
                  activeProperties: 8,
                  overallRating: 4.8,
                  pendingRequests: 3,
                ),
              ),
            ),
            _ => AppScaffold(
              showBackButton: false,
              contentWidth: SokounContentWidth.wide,
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: SokounAdaptiveGrid(
                  children: [
                    for (int i = 0; i < 3; i++)
                      TenantPropertyCard(
                        title: locale == 'ar'
                            ? 'شقة واسعة بإضاءة طبيعية في المعادي'
                            : 'Bright apartment in Maadi',
                        rating: '4.8',
                        area: locale == 'ar' ? '١٢٠ م²' : '120 m²',
                        price: locale == 'ar'
                            ? '١٨٬٠٠٠ ج.م / شهر'
                            : '18,000 EGP / month',
                        icon: Icons.apartment_rounded,
                      ),
                  ],
                ),
              ),
            ),
          };
          await tester.pumpWidget(
            EasyLocalization(
              supportedLocales: Languages.supportedLocales,
              path: Languages.translationsPath,
              startLocale: Locale(locale),
              saveLocale: false,
              assetLoader: const _ReviewTranslations(),
              child: ScreenUtilInit(
                designSize: const Size(360, 690),
                enableScaleWH: () => false,
                enableScaleText: () => false,
                fontSizeResolver: (size, _) => size.toDouble(),
                builder: (context, _) => MaterialApp(
                  theme: SokounTheme.light,
                  locale: context.locale,
                  supportedLocales: context.supportedLocales,
                  localizationsDelegates: context.localizationDelegates,
                  home: RepaintBoundary(child: screen),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          if (output.isNotEmpty) {
            final RenderRepaintBoundary boundary = tester.renderObject(
              find.byType(RepaintBoundary).first,
            );
            await tester.runAsync(() async {
              final ui.Image image = await boundary.toImage();
              final bytes = await image.toByteData(
                format: ui.ImageByteFormat.png,
              );
              await Directory(output).create(recursive: true);
              await File(
                '$output/$subject-$locale-${width.toInt()}.png',
              ).writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
        });
      }
    }
  }
}

class _ReviewTranslations extends AssetLoader {
  const _ReviewTranslations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
