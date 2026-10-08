import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_collection_filter.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_listing_categories.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorite_property_filter.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorites_data.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/saved_properties_response.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_offer_row.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_property_card.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/property_search_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import 'package:sokoun_app/shared_widgets/property_card_summary.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'helpers/home_page_test_dependencies.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/shared_preferences'),
      (call) async => call.method == 'getAll' ? <String, Object>{} : true,
    );
    messenger.setMockMethodCallHandler(
      const MethodChannel('dev.fluttercommunity.plus/connectivity'),
      (_) async => ['wifi'],
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
  setUp(() async {
    await injector.reset();
    registerHomePageTestDependencies();
  });
  tearDown(() => injector.reset());

  test(
    'owner categories use offers, preserve unavailable allocations and never guess legacy types',
    () {
      final inventory = _mixedInventory();
      for (final category in [
        RentalListingCategory.roomGroup,
        RentalListingCategory.bed,
      ]) {
        expect(
          RentalCollectionFilter.matchesProperty(
            category: category,
            inventory: inventory,
          ),
          isTrue,
        );
      }
      for (final category in [
        RentalListingCategory.room,
        RentalListingCategory.entireProperty,
      ]) {
        expect(
          RentalCollectionFilter.matchesProperty(
            category: category,
            inventory: inventory,
          ),
          isFalse,
        );
      }
      expect(
        RentalCollectionFilter.matchesProperty(
          category: RentalListingCategory.unspecified,
        ),
        isTrue,
      );
      expect(
        RentalCollectionFilter.matchesProperty(
          category: RentalListingCategory.entireProperty,
        ),
        isFalse,
      );
      expect(
        RentalCollectionFilter.matchesProperty(
          category: RentalListingCategory.bed,
          inventory: inventory.copyWith(
            offers: [bedOffer.copyWith(availability: 'rented', archived: true)],
          ),
        ),
        isTrue,
      );
    },
  );

  test(
    'favorites project matching saved offers once per property and retain unavailable beds',
    () {
      final favorite = _favorite('mixed', _mixedInventory());
      for (final category in [
        RentalListingCategory.bed,
        RentalListingCategory.roomGroup,
      ]) {
        final results = FavoritePropertyFilter.apply(
          [favorite, favorite],
          const PropertySearchFilters.initial(),
          category: category,
        );
        expect(results, hasLength(1));
        expect(results.single.savedOffers, hasLength(1));
        expect(results.single.savedOffers.single.scope, category.scope);
      }
      final unavailable = favorite.copyWith(
        savedOffers: [
          favorite.savedOffers.first.copyWith(availability: 'unavailable'),
        ],
      );
      final result = FavoritePropertyFilter.apply(
        [unavailable],
        const PropertySearchFilters.initial(),
        category: RentalListingCategory.bed,
      );
      expect(result.single.savedOffers.single.availability, 'unavailable');
      expect(
        favorite.savedOffers,
        hasLength(2),
      ); // Projection never changes the cached source.
    },
  );

  test(
    'missing saved snapshots and legacy room listings remain unspecified',
    () {
      final legacy = const FavoritePropertyContent.initial().copyWith(
        id: 'legacy',
        propertyType: 'room',
      );
      final missing = legacy.copyWith(
        id: 'missing-snapshot',
        rentalSchemaVersion: 1,
        rentalSummary: const RentalListingSummary(count: 1, scopes: ['bed']),
      );
      expect(
        FavoritePropertyFilter.apply(
          [legacy, missing],
          const PropertySearchFilters.initial(),
          category: RentalListingCategory.bed,
        ),
        isEmpty,
      );
      expect(
        FavoritePropertyFilter.apply(
          [legacy, missing],
          const PropertySearchFilters.initial(),
          category: RentalListingCategory.entireProperty,
        ),
        isEmpty,
      );
      expect(
        FavoritePropertyFilter.apply(
          [legacy, missing],
          const PropertySearchFilters.initial(),
          category: RentalListingCategory.unspecified,
        ),
        hasLength(2),
      );
    },
  );

  test('favorite term filters use the saved offer and its price period', () {
    final favorite = _favorite(
      'rooms',
      rentalInventory(offers: independentRooms),
    );
    final result = FavoritePropertyFilter.apply(
      [favorite],
      const PropertySearchFilters.initial(
        rentalScope: 'room',
        pricePeriod: 'weekly',
        priceMax: '2300',
      ),
    );
    expect(result.single.savedOffers.map((offer) => offer.offerId), [
      independentRooms.last.id,
    ]);
    expect(result.single.savedOffers.single.terms.price, '2200');
    expect(
      FavoritePropertyFilter.apply([
        favorite,
      ], const PropertySearchFilters.initial(priceMax: '2300')),
      isEmpty,
    );
  });

  testWidgets(
    'favorite card shows the saved group price instead of an unsaved bed minimum',
    (tester) async {
      final favorite =
          _favorite(
            'saved-group',
            rentalInventory(offers: [groupOffer]),
          ).copyWith(
            rentalSummary: const RentalListingSummary(
              count: 2,
              scopes: ['bed', 'room_group'],
              price: '1500',
              pricePeriod: 'monthly',
              priceScope: 'bed',
              startingFrom: true,
            ),
          );
      await _pump(tester, FavoritesScreen(initialItems: [favorite]));
      final expected =
          '${EgyptianPoundText.format('5000', period: 'monthly')} — ${groupOffer.scope!.priceBasis}';
      expect(
        find.descendant(
          of: find.byType(PropertyCardSummary),
          matching: find.text(expected),
        ),
        findsOneWidget,
      );
      expect(find.textContaining('1,500'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'favorite card keeps mixed prices separate and follows the filtered saved period',
    (tester) async {
      final favorite =
          _favorite(
            'saved-rooms',
            rentalInventory(offers: independentRooms),
          ).copyWith(
            rentalSummary: const RentalListingSummary(
              count: 2,
              scopes: ['room'],
              price: '1500',
              pricePeriod: 'monthly',
              priceScope: 'room',
              startingFrom: true,
            ),
          );
      await _pump(tester, FavoritesScreen(initialItems: [favorite]));
      expect(
        find.descendant(
          of: find.byType(PropertyCardSummary),
          matching: find.text(LocaleKeys.rentalSelectForPrice),
        ),
        findsOneWidget,
      );
      final filtered = FavoritePropertyFilter.apply(
        [favorite],
        const PropertySearchFilters.initial(pricePeriod: 'weekly'),
        category: RentalListingCategory.room,
      );
      await _pump(
        tester,
        FavoritesScreen(
          key: const ValueKey('weekly-saved-rooms'),
          initialItems: filtered,
        ),
      );
      final expected =
          '${EgyptianPoundText.format('2200', period: 'weekly')} — ${independentRooms.last.scope!.priceBasis}';
      expect(
        find.descendant(
          of: find.byType(PropertyCardSummary),
          matching: find.text(expected),
        ),
        findsOneWidget,
      );
      expect(find.textContaining('1,500'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'favorites category switching exposes matching saved offers and exact navigation',
    (tester) async {
      final items = [
        _favorite('mixed', _mixedInventory()),
        _favorite(
          'whole',
          rentalInventory(offers: [wholeOffer], mode: 'whole'),
        ),
        const FavoritePropertyContent.initial().copyWith(
          id: 'legacy',
          title: 'Historical room listing',
          propertyType: 'room',
        ),
      ];
      await _pump(tester, FavoritesScreen(initialItems: items));
      await _choose(tester, RentalListingCategory.bed);
      final card = tester.widget<FavoritePropertyCard>(
        find.byType(FavoritePropertyCard),
      );
      expect(card.item.id, 'mixed');
      expect(card.item.savedOffers.single.offerId, bedOffer.id);
      expect(find.byType(FavoriteOfferRow), findsOneWidget);
      final savedOffer = find.descendant(
        of: find.byType(FavoriteOfferRow),
        matching: find.byType(ListTile),
      );
      await tester.ensureVisible(savedOffer);
      await tester.pumpAndSettle();
      await tester.tap(savedOffer);
      await tester.pumpAndSettle();
      final details = tester.widget<PropertyDetailsScreen>(
        find.byType(PropertyDetailsScreen),
      );
      expect(details.propertyId, 'mixed');
      expect(details.offerId, bedOffer.id);
      Go.back();
      await tester.pumpAndSettle();
      await _choose(tester, RentalListingCategory.roomGroup);
      expect(
        tester
            .widget<FavoritePropertyCard>(find.byType(FavoritePropertyCard))
            .item
            .savedOffers
            .single
            .scopeValue,
        'room_group',
      );
      await _choose(tester, RentalListingCategory.unspecified);
      expect(
        tester
            .widget<FavoritePropertyCard>(find.byType(FavoritePropertyCard))
            .item
            .id,
        'legacy',
      );
      await _choose(tester, RentalListingCategory.all);
      expect(
        tester
            .widget<FavoritePropertyCard>(
              find.byType(FavoritePropertyCard).first,
            )
            .item
            .savedOffers,
        hasLength(2),
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'owner categories compose with review status and isolate offer actions',
    (tester) async {
      final accepted = _owner(
        'accepted',
        _mixedInventory(),
      ).copyWith(status: OwnerPropertyStatus.accepted);
      await _pump(
        tester,
        OwnerPropertiesScreen(
          initialProperties: [_owner('pending', _mixedInventory()), accepted],
        ),
      );
      await _choose(tester, RentalListingCategory.bed);
      expect(
        tester
            .widget<OwnerPropertyCard>(find.byType(OwnerPropertyCard))
            .property
            .id,
        'pending',
      );
      final editBed = find.text(LocaleKeys.rentalEditBed);
      await tester.ensureVisible(editBed);
      await tester.pumpAndSettle();
      expect(editBed, findsOneWidget);
      expect(find.text(LocaleKeys.rentalEditRoomGroup), findsNothing);
      final tabs = tester.widget<OwnerPropertiesStatusTabs>(
        find.byType(OwnerPropertiesStatusTabs),
      );
      tabs.onFilterSelected(OwnerPropertyFilter.accepted);
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<OwnerPropertyCard>(find.byType(OwnerPropertyCard))
            .property
            .id,
        'accepted',
      );
      expect(
        tester
            .widget<RentalListingCategories>(
              find.byType(RentalListingCategories),
            )
            .selected,
        RentalListingCategory.bed,
      );
      await _choose(tester, RentalListingCategory.roomGroup);
      expect(
        tester
            .widget<OwnerPropertyCard>(find.byType(OwnerPropertyCard))
            .category,
        RentalListingCategory.roomGroup,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'favorites can reach a later page even when the selected category has no loaded matches',
    (tester) async {
      final source = _FavoritesPages([
        [
          _favorite('room', rentalInventory(offers: [independentRooms.first])),
        ],
        [_favorite('bed', rentalInventory())],
      ]);
      injector.registerSingleton<FavoritesDataSource>(source);
      await _pump(tester, const FavoritesScreen());
      await _choose(tester, RentalListingCategory.bed);
      expect(find.text(LocaleKeys.rentalCategoryLoadedHint), findsOneWidget);
      if (source.requests.length == 1) {
        expect(find.byType(FavoritePropertyCard), findsNothing);
        await tester.ensureVisible(
          find.text(LocaleKeys.rentalCategoryLoadMore),
        );
        await tester.pumpAndSettle();
        if (source.requests.length == 1) {
          await tester.tap(find.text(LocaleKeys.rentalCategoryLoadMore));
          await tester.pumpAndSettle();
        }
      }
      expect(source.requests, [1, 2]);
      expect(
        tester
            .widget<FavoritePropertyCard>(find.byType(FavoritePropertyCard))
            .item
            .id,
        'bed',
      );
      final pagify = tester.widget<AppPagify<FavoritePropertyContent>>(
        find.byType(AppPagify<FavoritePropertyContent>),
      );
      expect(pagify.pagifyController.items.map((property) => property.id), [
        'room',
        'bed',
      ]);
      await _choose(tester, RentalListingCategory.room);
      expect(
        tester
            .widget<FavoritePropertyCard>(find.byType(FavoritePropertyCard))
            .item
            .id,
        'room',
      );
      expect(source.requests, [1, 2]);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'owner categories filter on the server before paging and retain property grouping',
    (tester) async {
      final source = _OwnerPages([
        [_owner('room', rentalInventory(offers: independentRooms))],
        [_owner('bed', _mixedInventory())],
      ]);
      injector.registerSingleton<OwnerPropertiesDataSource>(source);
      await _pump(tester, const OwnerPropertiesScreen());
      await _choose(tester, RentalListingCategory.bed);
      if (source.requests.length == 1) {
        await tester.ensureVisible(
          find.text(LocaleKeys.rentalCategoryLoadMore),
        );
        await tester.pumpAndSettle();
        if (source.requests.length == 1) {
          await tester.tap(find.text(LocaleKeys.rentalCategoryLoadMore));
          await tester.pumpAndSettle();
        }
      }
      expect(source.requests, [1, 1]);
      expect(source.categories, [
        RentalListingCategory.all,
        RentalListingCategory.bed,
      ]);
      expect(
        tester
            .widget<OwnerPropertyCard>(find.byType(OwnerPropertyCard))
            .property
            .id,
        'bed',
      );
      await _choose(tester, RentalListingCategory.roomGroup);
      expect(
        tester
            .widget<OwnerPropertyCard>(find.byType(OwnerPropertyCard))
            .property
            .id,
        'bed',
      );
      expect(source.requests, [1, 1, 1]);
      expect(source.categories.last, RentalListingCategory.roomGroup);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('search categories stay visible and scope requests stay gated', (
    tester,
  ) async {
    final source = _SearchCategorySource();
    injector.registerSingleton<PropertySearchDataSource>(source);
    await _pump(
      tester,
      const TenantSearchResultsScreen(
        initialFilters: PropertySearchFilters.initial(
          search: 'Near transport',
          pricePeriod: 'monthly',
        ),
      ),
    );
    final categories = tester.widget<RentalListingCategories>(
      find.byType(RentalListingCategories),
    );
    expect(categories.includeUnspecified, isFalse);
    expect(
      categories.scopeSearchUnavailable,
      !RentalOfferCapabilities.configured.canSearch,
    );
    final bed = tester.widget<SokounSelectionChip>(
      _chip(RentalListingCategory.bed),
    );
    if (RentalOfferCapabilities.configured.canSearch) {
      expect(bed.onPressed, isNotNull);
      await _choose(tester, RentalListingCategory.bed);
      expect(source.requests.last.rentalScope, 'bed');
      expect(source.requests.last.pricePeriod, 'monthly');
      expect(source.requests.last.search, 'Near transport');
    } else {
      expect(bed.onPressed, isNull);
      expect(
        find.text(LocaleKeys.rentalCategorySearchUnavailable),
        findsOneWidget,
      );
      expect(source.requests.single.rentalScope, isEmpty);
    }
    expect(tester.takeException(), isNull);
  });

  for (final owner in [false, true]) {
    for (final locale in ['en', 'ar']) {
      for (final dark in [false, true]) {
        for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
          for (final scale in [1.0, 1.3, 2.0]) {
            testWidgets(
              '${owner ? 'owner' : 'favorites'} categories $locale ${dark ? 'dark' : 'light'} ${width.toInt()} scale $scale',
              (tester) async {
                final capture = GlobalKey();
                await _pump(
                  tester,
                  owner
                      ? OwnerPropertiesScreen(
                          initialProperties: [
                            _owner('mixed', _mixedInventory()),
                          ],
                        )
                      : FavoritesScreen(
                          initialItems: [_favorite('mixed', _mixedInventory())],
                        ),
                  width: width,
                  scale: scale,
                  locale: locale,
                  dark: dark,
                  capture: capture,
                );
                expect(
                  Directionality.of(
                    tester.element(find.byType(RentalListingCategories)),
                  ),
                  locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr,
                );
                await _choose(tester, RentalListingCategory.bed);
                expect(tester.takeException(), isNull);
                if (owner) {
                  expect(
                    tester
                        .widget<OwnerPropertyCard>(
                          find.byType(OwnerPropertyCard),
                        )
                        .category,
                    RentalListingCategory.bed,
                  );
                } else {
                  expect(
                    tester
                        .widget<FavoritePropertyCard>(
                          find.byType(FavoritePropertyCard),
                        )
                        .item
                        .savedOffers
                        .single
                        .scopeValue,
                    'bed',
                  );
                }
                if (scale == 1 &&
                    ((width == 390 && locale == 'en' && !dark) ||
                        (width == 768 && locale == 'ar' && dark))) {
                  await _capture(
                    tester,
                    capture,
                    '${owner ? 'owner' : 'favorites'}-$locale-${width.toInt()}-${dark ? 'dark' : 'light'}',
                  );
                }
              },
            );
          }
        }
      }
    }
  }
}

RentalInventory _mixedInventory() => rentalInventory(
  offers: [
    bedOffer.copyWith(name: 'Window bed'),
    groupOffer.copyWith(
      name: 'Two rooms together',
      roomRefs: ['room-b', 'room-c'],
    ),
  ],
);

FavoritePropertyContent _favorite(String id, RentalInventory inventory) =>
    const FavoritePropertyContent.initial().copyWith(
      id: id,
      title: 'Apartment near transport',
      propertyType: 'apartment',
      isSaved: true,
      rentalSchemaVersion: 1,
      city: 'Cairo',
      area: 120,
      savedOffers: inventory.offers
          .map(
            (offer) => RentalSelection.fromOffer(
              propertyId: id,
              inventory: inventory,
              offer: offer,
            ),
          )
          .toList(),
    );

OwnerPropertyContent _owner(String id, RentalInventory inventory) =>
    OwnerPropertyContent.initial().copyWith(
      id: id,
      title: 'Apartment near transport',
      propertyType: 'apartment',
      location: 'Cairo',
      rentalInventory: inventory,
      status: OwnerPropertyStatus.pending,
    );

Finder _chip(RentalListingCategory category) => find.descendant(
  of: find.byType(RentalListingCategories),
  matching: find.widgetWithText(
    SokounSelectionChip,
    RentalListingCategories.label(category),
  ),
);

Future<void> _choose(
  WidgetTester tester,
  RentalListingCategory category,
) async {
  await tester.ensureVisible(_chip(category));
  await tester.pumpAndSettle();
  await tester.tap(_chip(category));
  await tester.pumpAndSettle();
}

Future<void> _pump(
  WidgetTester tester,
  Widget screen, {
  double width = 390,
  double scale = 1,
  String locale = 'en',
  bool dark = false,
  GlobalKey? capture,
}) async {
  tester.view.physicalSize = Size(width, width >= 600 ? 1024 : 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('en'), Locale('ar')],
      path: 'unused',
      saveLocale: false,
      startLocale: Locale(locale),
      assetLoader: const _Translations(),
      child: ScreenUtilInit(
        designSize: const Size(390, 844),
        enableScaleWH: () => false,
        enableScaleText: () => false,
        builder: (context, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          theme: dark ? SokounTheme.dark : SokounTheme.light,
          locale: context.locale,
          supportedLocales: context.supportedLocales,
          localizationsDelegates: context.localizationDelegates,
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: true,
            ),
            child: RepaintBoundary(key: capture, child: child!),
          ),
          home: screen,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _capture(
  WidgetTester tester,
  GlobalKey capture,
  String name,
) async {
  await tester.runAsync(() async {
    final boundary =
        capture.currentContext!.findRenderObject()! as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 1);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    final directory = Directory(
      '${Directory.systemTemp.path}/sokoun-listing-category-renders',
    )..createSync(recursive: true);
    File(
      '${directory.path}/$name.png',
    ).writeAsBytesSync(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

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

class _FavoritesPages implements FavoritesDataSource {
  _FavoritesPages(this.pages);
  final List<List<FavoritePropertyContent>> pages;
  final List<int> requests = [];
  @override
  String get cacheKey => 'category-favorites-test';
  @override
  Future<SavedPropertiesResponse> getSavedProperties({
    required int page,
  }) async => (await getSavedPropertiesPage(page: page)).$1;
  @override
  Future<(SavedPropertiesResponse, PaginationData)> getSavedPropertiesPage({
    required int page,
  }) async {
    requests.add(page);
    return (
      SavedPropertiesResponse(
        count: pages.expand((items) => items).length,
        perPage: 1,
        totalPages: pages.length,
        results: pages[page - 1],
      ),
      PaginationData(perPage: 1, totalPages: pages.length),
    );
  }
}

class _OwnerPages implements OwnerPropertiesDataSource {
  _OwnerPages(this.pages);
  final List<List<OwnerPropertyContent>> pages;
  final List<int> requests = [];
  final List<RentalListingCategory> categories = [];
  @override
  String get cacheKey => 'category-owner-test';
  @override
  String get governoratesCacheKey => 'category-owner-governorates-test';
  @override
  String citiesCacheKey(String governorateId) => 'category-owner-cities-test';
  @override
  Future<OwnerPropertyLocationsResponse> getGovernorates() async =>
      const OwnerPropertyLocationsResponse.initial();
  @override
  Future<OwnerPropertyLocationsResponse> getCities({
    required String governorateId,
    required String search,
  }) async => const OwnerPropertyLocationsResponse.initial();
  @override
  Future<(List<OwnerPropertyContent>, PaginationData)> getOwnedPropertiesPage({
    required int page,
    required OwnerPropertyFilter filter,
    RentalListingCategory category = RentalListingCategory.all,
  }) async {
    requests.add(page);
    categories.add(category);
    final filtered = pages
        .expand((items) => items)
        .where(
          (property) => RentalCollectionFilter.matchesProperty(
            category: category,
            inventory: property.rentalInventory,
            summary: property.rentalSummary,
            scopes: property.rentalScopes,
          ),
        )
        .toList();
    return (
      filtered.skip(page - 1).take(1).toList(),
      PaginationData(perPage: 1, totalPages: filtered.length),
    );
  }
}

class _SearchCategorySource implements PropertySearchDataSource {
  final List<PropertySearchFilters> requests = [];
  @override
  String cacheKeyFor(PropertySearchFilters filters) => filters.cacheKey;
  @override
  Future<(PropertySearchResponseModel, PaginationData)> getPropertiesPage(
    PropertySearchFilters filters, {
    CancelToken? cancelToken,
  }) async {
    requests.add(filters);
    return (
      const PropertySearchResponseModel.initial(),
      PaginationData(perPage: filters.pageSize, totalPages: 1),
    );
  }
}
