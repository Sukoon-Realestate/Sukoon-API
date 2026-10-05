import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_property_card.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/filter_price_range_section.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/property_filter_label_resolver.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/price_and_rating.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/rental_details.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('UI_REVIEW_DIR');

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold', 'Black']) {
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

  final revenue = OwnerRevenueContent.fromJson({
    'total_this_month': 36000.75,
    'formatted_total': '36,000 SAR',
    'currency': 'SAR',
    'properties': [
      {
        'id': 'property',
        'title': 'October rent',
        'amount': 6500.5,
        'formatted_amount': '6,500 ر.س',
        'currency': 'ر.س',
        'status': 'due',
      },
    ],
    'recent_transactions': [
      {
        'id': 'credit',
        'title': 'Rent payment',
        'amount': 6500.5,
        'formatted_amount': '6,500 USD',
        'currency': 'USD',
        'is_credit': true,
      },
      {
        'id': 'debit',
        'title': 'Maintenance',
        'amount': -125.75,
        'currency': 'AED',
        'is_credit': false,
      },
    ],
  });

  Widget properties() {
    final property = TenantPropertyDetailsContent.fromModel(
      PropertyDetailsModel.fromJson({
        'price': '6500.75',
        'price_period': 'monthly',
        'deposit': '1000.5',
      }),
    );
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12,
        children: [
          TenantPropertyPriceAndRating(property: property),
          TenantPropertyRentalDetails(property: property),
          VisitDetailsExtra(
            details: const TenantVisitDetailsContent.initial().copyWith(
              price: '6500.25',
            ),
          ),
          OwnerPropertyCard(
            property: OwnerPropertyContent.initial().copyWith(
              monthlyPrice: 6500.75,
              pricePeriod: 'monthly',
            ),
            onEditPressed: () {},
            onRejectedPressed: () {},
            onDeletePressed: () {},
          ),
          FavoritePropertyCard(
            item: const FavoritePropertyContent.initial().copyWith(
              price: '6500.5',
              pricePeriod: 'weekly',
            ),
            onRemove: () {},
          ),
        ],
      ),
    );
  }

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0, 1024.0]) {
      for (final scale in [1.0, 2.0]) {
        for (final subject in ['revenue', 'properties']) {
          testWidgets('EGP $subject $locale width=$width scale=$scale', (
            tester,
          ) async {
            tester.view.physicalSize = Size(width, 1100);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            await tester.pumpWidget(
              _localized(
                Builder(
                  builder: (_) => Scaffold(
                    body: subject == 'revenue'
                        ? OwnerRevenueContentView(data: revenue)
                        : properties(),
                  ),
                ),
                locale: locale,
                scale: scale,
              ),
            );
            await tester.pumpAndSettle();
            final symbol = locale == 'ar' ? 'ج.م' : 'EGP';
            expect(EgyptianPoundText.symbol, symbol);
            if (subject == 'revenue') {
              expect(find.text('36,000.75 $symbol'), findsOneWidget);
              expect(find.text('6,500.5 $symbol'), findsOneWidget);
              expect(find.text('+6,500.5 $symbol'), findsOneWidget);
              expect(find.text('-125.75 $symbol'), findsOneWidget);
              expect(find.textContaining('SAR'), findsNothing);
              expect(find.textContaining('ر.س'), findsNothing);
              expect(find.textContaining('USD'), findsNothing);
              expect(find.textContaining('AED'), findsNothing);
            } else {
              expect(find.text('1,000.5 $symbol'), findsOneWidget);
              expect(find.text('6,500.25 $symbol'), findsOneWidget);
              expect(
                find.text(EgyptianPoundText.format(6500.75, period: 'monthly')),
                findsOneWidget,
              );
              expect(
                find.text(EgyptianPoundText.format(6500.5, period: 'weekly')),
                findsOneWidget,
              );
            }
            expect(tester.takeException(), isNull);
            if (output.isNotEmpty && width == 390) {
              final RenderRepaintBoundary boundary = tester.renderObject(
                find.byType(RepaintBoundary).first,
              );
              await tester.runAsync(() async {
                final image = await boundary.toImage();
                final bytes = await image.toByteData(
                  format: ui.ImageByteFormat.png,
                );
                await Directory(output).create(recursive: true);
                await File(
                  '$output/currency-$subject-$locale-text-$scale.png',
                ).writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            await tester.pumpWidget(const SizedBox.shrink());
          });
        }
      }
    }

    testWidgets('price inputs and active filters specify EGP in $locale', (
      tester,
    ) async {
      final min = TextEditingController(text: '5000');
      final max = TextEditingController(text: '10000');
      PropertySearchFilters filters = const PropertySearchFilters.initial(
        priceMin: '5000',
        priceMax: '10000',
      );
      tester.view.physicalSize = const Size(320, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        _localized(
          Scaffold(
            body: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: FilterPriceRangeSection(
                filters: filters,
                minPriceController: min,
                maxPriceController: max,
                onFiltersChanged: (value) => filters = value,
              ),
            ),
          ),
          locale: locale,
          scale: 2,
        ),
      );
      await tester.pumpAndSettle();
      final symbol = locale == 'ar' ? 'ج.م' : 'EGP';
      expect(
        find.text('${LocaleKeys.tenantFilterFrom} ($symbol)'),
        findsOneWidget,
      );
      expect(
        find.text('${LocaleKeys.tenantFilterTo} ($symbol)'),
        findsOneWidget,
      );
      const resolver = PropertyFilterLabelResolver(
        PropertyFilterOptionsModel.initial(),
      );
      expect(
        resolver.labelFor(
          const PropertySearchFilterEntry(id: 'price_min', value: '5000.75'),
        ),
        '${LocaleKeys.tenantFilterFrom} 5,000.75 $symbol',
      );
      await tester.enterText(find.byType(TextField).first, '6000');
      expect(filters.priceMin, '6000');
      expect(filters.priceMax, '10000');
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      min.dispose();
      max.dispose();
    });
  }
}

Widget _localized(
  Widget screen, {
  required String locale,
  required double scale,
}) => EasyLocalization(
  supportedLocales: Languages.supportedLocales,
  path: Languages.translationsPath,
  startLocale: Locale(locale),
  saveLocale: false,
  assetLoader: const _Translations(),
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
      home: MediaQuery(
        data: MediaQuery.of(context).copyWith(
          textScaler: TextScaler.linear(scale),
          disableAnimations: true,
        ),
        child: RepaintBoundary(child: screen),
      ),
    ),
  ),
);

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
