import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/property_search_data.dart';
import 'package:sokoun_app/features/tenant/home/data/rental_home_section_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/rental_home_section_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/rental_home/rental_home_sections.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/rental_home/rental_home_section.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/rental_home/rental_home_empty_state.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/search_result_card.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _DiscoveryRepository repository;
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity'),
          (_) async => ['wifi'],
        );
  });
  setUp(() async {
    await injector.reset();
    repository = _DiscoveryRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    injector.registerSingleton<PropertySearchDataSource>(const _EmptySearch());
  });
  tearDown(() => injector.reset());

  Future<void> pump(WidgetTester tester, Widget home) async {
    tester.view.physicalSize = const Size(390, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: const [Locale('en')],
        path: 'unused',
        saveLocale: false,
        startLocale: const Locale('en'),
        assetLoader: _Translations(
          jsonDecode(
                File(
                  '../../packages/core/assets/translations/en.json',
                ).readAsStringSync(),
              )
              as Map<String, dynamic>,
        ),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          enableScaleWH: () => false,
          enableScaleText: () => false,
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            theme: SokounTheme.light,
            locale: context.locale,
            supportedLocales: context.supportedLocales,
            localizationsDelegates: context.localizationDelegates,
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(disableAnimations: true),
              child: child!,
            ),
            home: Scaffold(body: SingleChildScrollView(child: home)),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  test(
    'section requests reuse the properties endpoint and complete cache contract',
    () {
      final request = RentalHomeSectionData.request(
        scope: RentalScope.bed,
        period: PropertyPricePeriod.monthly,
        capabilities: offersEnabled,
      );
      expect(request.api, 'properties/');
      expect(request.httpRequestType, HttpRequestType.get);
      expect(request.queryParameters, containsPair('rental_scope', 'bed'));
      expect(request.queryParameters, containsPair('price_period', 'monthly'));
      expect(request.queryParameters, containsPair('page_size', 2));
      expect(request.queryParameters, containsPair('rental_offers_version', 1));
      final other = RentalHomeSectionData.request(
        scope: RentalScope.bed,
        period: PropertyPricePeriod.weekly,
        capabilities: offersEnabled,
      );
      expect(request.cacheKey, isNot(other.cacheKey));
      final parsed = request.mapper!(repository.response('bed', 'monthly'));
      expect(parsed.count, 9);
      expect(parsed.results, hasLength(1));
      expect(parsed.results.single.rentalSummary!.count, 3);
      expect(request.fromCacheJson!(request.toJson!(parsed)), parsed);
      final all = RentalHomeSectionData.filters(
        RentalScope.bed,
        PropertyPricePeriod.monthly,
      );
      expect(all.pageSize, 10);
      expect(all.copyWith(page: 2, search: 'Cairo').rentalScope, 'bed');
      expect(all.copyWith(page: 2, search: 'Cairo').pricePeriod, 'monthly');
    },
  );
  test('disabled discovery makes no network request', () async {
    final cubit = RentalHomeSectionCubit(
      scope: RentalScope.room,
      period: PropertyPricePeriod.monthly,
    );
    addTearDown(cubit.close);
    await cubit.load();
    expect(repository.requests, isEmpty);
    expect(cubit.state.isError, isTrue);
  });
  test(
    'duplicate property rows and incompatible summaries cannot become a catalog',
    () {
      final request = RentalHomeSectionData.request(
        scope: RentalScope.bed,
        period: PropertyPricePeriod.monthly,
        capabilities: offersEnabled,
      );
      final valid = repository.response('bed', 'monthly');
      final item = (valid['results'] as List).single as Map<String, dynamic>;
      for (final invalid in [
        {
          ...valid,
          'results': [item, item],
        },
        {...valid, 'count': null},
        {...valid, 'count': 0},
        {...valid, 'results': []},
        {...valid, 'next': null},
        {
          ...valid,
          'results': [
            {
              ...item,
              'rental_summary': {
                ...item['rental_summary'] as Map,
                'price_period': 'weekly',
              },
            },
          ],
        },
        {
          ...valid,
          'results': [
            {
              ...item,
              'rental_summary': {
                ...item['rental_summary'] as Map,
                'scopes': ['room', 'bed'],
              },
            },
          ],
        },
      ]) {
        expect(() => request.mapper!(invalid), throwsFormatException);
      }
      final empty = request.mapper!({
        'count': 0,
        'next': null,
        'previous': null,
        'results': [],
      });
      expect(empty.results, isEmpty);
      expect(empty.count, 0);
    },
  );
  testWidgets(
    'period changes replace four query owners once and View all retains filters',
    (tester) async {
      await pump(tester, const RentalHomeSections(capabilities: offersEnabled));
      expect(repository.requests, hasLength(4));
      expect(
        repository.requests
            .map((r) => r.queryParameters!['rental_scope'])
            .toSet(),
        RentalScope.values.map((s) => s.value).toSet(),
      );
      expect(
        repository.requests.every(
          (r) => r.queryParameters!['price_period'] == 'monthly',
        ),
        isTrue,
      );
      expect(find.byType(SearchResultCard), findsNWidgets(4));
      expect(find.text('Showing 1 of 9 properties'), findsNWidgets(4));
      await tester.tap(find.text(PropertyPricePeriod.weekly.label).first);
      await tester.pumpAndSettle();
      expect(repository.requests, hasLength(8));
      expect(
        repository.requests
            .skip(4)
            .every((r) => r.queryParameters!['price_period'] == 'weekly'),
        isTrue,
      );
      final section = find.byWidgetPredicate(
        (w) => w is RentalHomeSection && w.scope == RentalScope.bed,
      );
      final viewAll = find.descendant(
        of: section,
        matching: find.widgetWithText(TextButton, LocaleKeys.tenantHomeViewAll),
      );
      await tester.ensureVisible(viewAll);
      await tester.tap(viewAll);
      await tester.pumpAndSettle();
      final screen = tester.widget<TenantSearchResultsScreen>(
        find.byType(TenantSearchResultsScreen),
      );
      expect(screen.initialFilters.rentalScope, 'bed');
      expect(screen.initialFilters.pricePeriod, 'weekly');
      expect(screen.initialFilters.pageSize, 10);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'a preview card opens property details with filters and no automatic offer choice',
    (tester) async {
      await pump(
        tester,
        const RentalHomeSection(
          scope: RentalScope.bed,
          period: PropertyPricePeriod.monthly,
          capabilities: offersEnabled,
        ),
      );
      await tester.tap(find.text('Discovery property').first);
      await tester.pumpAndSettle();
      final screen = tester.widget<PropertyDetailsScreen>(
        find.byType(PropertyDetailsScreen),
      );
      expect(screen.propertyId, 'property-a');
      expect(screen.offerId, isNull);
      expect(screen.confirmedSelection, isNull);
      expect(screen.searchPreferences!.rentalScope, 'bed');
      expect(screen.searchPreferences!.pricePeriod, 'monthly');
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'empty success uses contextual Lottie and failures remain retryable',
    (tester) async {
      repository.empty = true;
      await pump(
        tester,
        const RentalHomeSection(
          scope: RentalScope.room,
          period: PropertyPricePeriod.monthly,
          capabilities: offersEnabled,
        ),
      );
      expect(find.byType(RentalHomeEmptyState), findsOneWidget);
      expect(find.byType(ExceptionView), findsNothing);
      expect(find.byType(SearchResultCard), findsNothing);
      await tester.pumpWidget(const SizedBox());
      repository.empty = false;
      repository.failReads = true;
      await pump(
        tester,
        const RentalHomeSection(
          scope: RentalScope.bed,
          period: PropertyPricePeriod.monthly,
          capabilities: offersEnabled,
        ),
      );
      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byType(RentalHomeEmptyState), findsNothing);
      repository.failReads = false;
      final exception = tester.widget<ExceptionView>(
        find.byType(ExceptionView),
      );
      await exception.onRetry!();
      await tester.pumpAndSettle();
      expect(find.byType(SearchResultCard), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  test('disposing a query owner ignores its late response', () async {
    repository.pause = Completer<void>();
    final cubit = RentalHomeSectionCubit(
      scope: RentalScope.bed,
      period: PropertyPricePeriod.monthly,
      capabilities: offersEnabled,
    );
    final pending = cubit.load();
    await cubit.close();
    repository.pause!.complete();
    await pending;
    expect(cubit.state.isSuccess, isFalse);
  });
}

class _DiscoveryRepository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  bool empty = false, failReads = false;
  Completer<void>? pause;
  Map<String, dynamic> response(String scope, String period) => {
    'count': empty ? 0 : 9,
    'next': empty ? null : '?page=2',
    'previous': null,
    'results': empty
        ? []
        : [
            rentalProperty(
                  summary: RentalListingSummary(
                    count: 3,
                    scopes: [scope],
                    labels: ['Named accommodation'],
                    price: '1500',
                    pricePeriod: period,
                    priceScope: scope,
                    startingFrom: true,
                  ),
                )
                .copyWith(
                  title: 'Discovery property',
                  mainImage: '',
                  images: [],
                )
                .toJson(),
          ],
  };
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.api == 'properties/') {
      requests.add(params);
      if (pause != null) await pause!.future;
      if (failReads) return const Error(ServerFailure('offline'));
    }
    final json = params.api == 'properties/'
        ? response(
            params.queryParameters!['rental_scope'],
            params.queryParameters!['price_period'],
          )
        : params.api.endsWith('/reviews/')
        ? <String, dynamic>{}
        : params.api == 'properties/property-a/'
        ? rentalProperty(
            inventory: rentalInventory(),
          ).copyWith(mainImage: '', images: [], video: '').toJson()
        : <String, dynamic>{};
    try {
      return Success(
        BaseModel<T>(key: '', msg: '', data: params.mapper!(json)),
      );
    } catch (e) {
      return Error(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _Translations extends AssetLoader {
  const _Translations(this.values);
  final Map<String, dynamic> values;
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => values;
}

class _EmptySearch implements PropertySearchDataSource {
  const _EmptySearch();
  @override
  String cacheKeyFor(PropertySearchFilters filters) => filters.cacheKey;
  @override
  Future<(PropertySearchResponseModel, PaginationData)> getPropertiesPage(
    PropertySearchFilters filters, {
    CancelToken? cancelToken,
  }) async => (
    const PropertySearchResponseModel.initial(),
    PaginationData(perPage: filters.pageSize, totalPages: 1),
  );
}
