import 'dart:convert';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_type_selector.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/property_review_summary.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_rating_summary.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Repository repository;

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
    messenger.setMockMethodCallHandler(
      const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
      (_) async => null,
    );
    await EasyLocalization.ensureInitialized();
    for (final language in ['en', 'ar']) {
      _translations[language] =
          jsonDecode(
                await rootBundle.loadString(
                  'packages/melos_core/assets/translations/$language.json',
                ),
              )
              as Map<String, dynamic>;
    }
  });
  setUp(() async {
    await injector.reset();
    repository = _Repository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });
  tearDown(() => injector.reset());

  Future<void> pump(WidgetTester tester, Widget child) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: const [Locale('en'), Locale('ar')],
        startLocale: const Locale('en'),
        fallbackLocale: const Locale('en'),
        saveLocale: false,
        path: 'packages/melos_core/assets/translations',
        assetLoader: const _Translations(),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            locale: context.locale,
            supportedLocales: context.supportedLocales,
            localizationsDelegates: context.localizationDelegates,
            home: Scaffold(body: child),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  test(
    'booking metadata uses the selected property and verification is independent',
    () {
      final model = PropertyDetailsModel.fromJson({
        'id': 'actual-property',
        'owner': {
          'id': 'actual-owner',
          'name': 'Actual owner',
          'is_verified': false,
        },
        'is_verified': true,
        'owner_is_verified': true,
        'price': '900',
        'price_period': 'daily',
        'bedrooms': 5,
      });
      final content = TenantPropertyDetailsContent.fromModel(model);
      final booking = VisitPropertyContent.fromPropertyDetails(content);
      expect(booking.id, 'actual-property');
      expect(booking.ownerId, 'actual-owner');
      expect(booking.meta, contains(content.price));
      expect(booking.meta, contains(content.pricePeriodLabel));
      expect(booking.meta, contains('5'));
      expect(booking.meta, isNot(contains('6500')));
      expect(content.isVerified, isTrue);
      expect(content.isOwnerVerified, isFalse);
      expect(content.isOwnershipVerified, isFalse);
      expect(PropertyDetailsModel.fromJson(model.toJson()), model);
      final verified = model.copyWith(
        isOwnerVerified: true,
        isOwnershipVerified: true,
      );
      expect(PropertyDetailsModel.fromJson(verified.toJson()), verified);
    },
  );

  testWidgets('ratings come from the summary API and are cached per property', (
    tester,
  ) async {
    await pump(tester, const PropertyRatingSummary(propertyId: 'first'));
    expect(find.text('4.6'), findsOneWidget);
    expect(find.text('(19)'), findsOneWidget);
    final params =
        repository.requests.single as CrudBaseParmas<PropertyReviewSummary>;
    expect(params.api, ApiConstants.propertyReviews('first'));
    expect(params.httpRequestType, HttpRequestType.get);
    expect(params.cacheKey, 'property_review_summary_first');
    const summary = PropertyReviewSummary(totalReviews: 19, averageRating: 4.6);
    expect(params.fromCacheJson!(params.toJson!(summary)), summary);
    await pump(tester, const PropertyRatingSummary(propertyId: 'second'));
    expect(
      repository.requests.last.api,
      ApiConstants.propertyReviews('second'),
    );
    expect(repository.requests.last.cacheKey, 'property_review_summary_second');
    expect(tester.takeException(), isNull);
  });

  testWidgets('missing review totals do not become a fabricated zero count', (
    tester,
  ) async {
    repository.summary = const {};
    await pump(
      tester,
      const PropertyRatingSummary(propertyId: 'missing-summary'),
    );
    expect(find.byIcon(Icons.star_rounded), findsNothing);
    expect(find.text('(0)'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'property type options use API labels and submit the matching slug',
    (tester) async {
      OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
          .copyWith(
            bedrooms: '2',
            bathrooms: '1',
            space: '100',
            floor: '3',
            rentalDuration: '6',
          );
      await pump(
        tester,
        AddPropertyTypeSelector(
          selectedValue: '',
          onSelected: (value) => form = form.copyWith(
            propertyType: value.name,
            propertyTypeValue: value.slug,
          ),
        ),
      );
      expect(find.text('API duplex'), findsOneWidget);
      expect(find.text('Apartment'), findsNothing);
      await tester.tap(find.text('API duplex'));
      expect(form.propertyType, 'API duplex');
      expect(form.propertyTypeApiValue, 'duplex');
      expect(form.toRequestBody()['property_type'], 'duplex');
      expect(repository.requests.single.api, ApiConstants.propertyTypes);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'availability loads server dates and preserves booked slots when saving',
    (tester) async {
      await pump(
        tester,
        OwnerAvailabilityScreen(
          ownerPropertyId: 'property-id',
          availabilityStartDate: DateTime(2026, 10, 2),
        ),
      );
      final params = repository.requests.single;
      expect(params.httpRequestType, HttpRequestType.get);
      expect(params.api, ApiConstants.ownerPropertyAvailability('property-id'));
      expect(params.queryParameters, {'week_start': '2026-09-28'});
      expect(
        params.cacheKey,
        'owner_property_availability_property-id_2026-09-28',
      );
      final content = tester.widget<OwnerAvailabilityContent>(
        find.byType(OwnerAvailabilityContent),
      );
      expect(content.days, hasLength(7));
      expect(content.days[content.selectedDayIndex].date, '2026-10-02');
      expect(content.slots.map((slot) => slot.time), [
        '09:30:00',
        '12:15:00',
        '17:45:00',
      ]);
      expect(content.slotStates, [
        OwnerAvailabilitySlotState.available,
        OwnerAvailabilitySlotState.booked,
        OwnerAvailabilitySlotState.unspecified,
      ]);
      content.onTimePressed(1);
      content.onTimePressed(2);
      await tester.pump();
      final updated = tester.widget<OwnerAvailabilityContent>(
        find.byType(OwnerAvailabilityContent),
      );
      expect(updated.slotStates[1], OwnerAvailabilitySlotState.booked);
      expect(updated.slotStates[2], OwnerAvailabilitySlotState.available);
      await updated.onSavePressed();
      final body = repository.requests.last.body!;
      expect(repository.requests.last.httpRequestType, HttpRequestType.put);
      expect(body['availability_date'], '2026-10-02');
      expect(body['slots'], [
        {'time': '09:30:00', 'is_enabled': true},
        {'time': '12:15:00', 'is_enabled': true},
        {'time': '17:45:00', 'is_enabled': true},
      ]);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('profile fallbacks show returned counts without sample facts', (
    tester,
  ) async {
    final owner = OwnerProfileContent.fromJson({
      'owner': {
        'full_name': 'Actual owner',
        'average_rating': 3.7,
        'reviews_count': 11,
        'is_verified': false,
      },
    });
    final menu = TenantProfileMenuItemsContent.fromJson({
      'contracts': {'count': 8},
      'reviews': {'count': 13},
    });
    await pump(
      tester,
      ListView(
        children: [
          OwnerProfileHeaderCard(profile: owner),
          TenantProfileActions(menuItems: menu),
        ],
      ),
    );
    expect(find.text('Rated 3.7 from 11 reviews'), findsOneWidget);
    expect(find.text('8 active contracts'), findsOneWidget);
    expect(find.text('13 reviews'), findsOneWidget);
    expect(find.text('Not set yet'), findsOneWidget);
    expect(find.byIcon(Icons.check_rounded), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('notification analytics hides unavailable metrics', (
    tester,
  ) async {
    final analytics = OwnerPropertyAnalyticsContent.initial().copyWith(
      views: 321,
    );
    expect(analytics.hasDetails, isFalse);
    expect(
      OwnerPropertyAnalyticsContent.fromJson({'views': 321}).hasDetails,
      isFalse,
    );
    expect(
      OwnerPropertyAnalyticsContent.fromJson(analytics.toJson()),
      analytics,
    );
    await pump(
      tester,
      OwnerPropertyAnalyticsScreen(
        property: OwnerPropertyContent.initial().copyWith(
          title: 'Actual property',
        ),
        analytics: analytics,
      ),
    );
    expect(find.text('321'), findsOneWidget);
    expect(find.byType(OwnerAnalyticsMetricCard), findsOneWidget);
    expect(find.byType(OwnerAnalyticsBarChart), findsNothing);
    expect(find.text('0%'), findsNothing);
    expect(tester.takeException(), isNull);
    await pump(tester, const OwnerAnalyticsBarChart(values: [0, 0]));
    expect(tester.takeException(), isNull);
  });

  testWidgets('empty availability is distinct from a failed request', (
    tester,
  ) async {
    repository.schedule = const {'days': []};
    await pump(
      tester,
      OwnerAvailabilityScreen(
        ownerPropertyId: 'empty',
        availabilityStartDate: DateTime(2026, 10, 2),
      ),
    );
    expect(find.byType(OwnerAvailabilityEmptyState), findsOneWidget);
    expect(find.byType(OwnerAvailabilityContent), findsNothing);
    expect(find.byType(ExceptionView), findsNothing);
    repository.fail = true;
    await pump(
      tester,
      OwnerAvailabilityScreen(
        ownerPropertyId: 'failed',
        availabilityStartDate: DateTime(2026, 10, 2),
        key: const ValueKey('failed'),
      ),
    );
    expect(find.byType(ExceptionView), findsOneWidget);
    expect(find.byType(OwnerAvailabilityEmptyState), findsNothing);
    expect(tester.takeException(), isNull);
  });
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations[locale.languageCode]!;
}

class _Repository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  bool fail = false;
  Map<String, dynamic> summary = {'total_reviews': 19, 'average_rating': 4.6};
  Map<String, dynamic> schedule = {
    'week_start': '2026-09-28',
    'week_end': '2026-10-04',
    'days': [
      {
        'date': '2026-10-02',
        'day': 'friday',
        'slots': [
          {
            'id': 'available',
            'time': '09:30:00',
            'is_enabled': true,
            'state': 'available',
          },
          {
            'id': 'booked',
            'time': '12:15:00',
            'is_enabled': true,
            'state': 'booked',
            'visit': {'id': 'visit-id'},
          },
          {
            'id': 'disabled',
            'time': '17:45:00',
            'is_enabled': false,
            'state': 'unspecified',
          },
        ],
      },
    ],
  };

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    if (fail) return const Error(Failure('Request failed'));
    final Map<String, dynamic> json = params.api.endsWith('/reviews/')
        ? {'summary': summary}
        : params.api == ApiConstants.propertyTypes
        ? {
            'count': 1,
            'results': [
              {'id': 'duplex-id', 'name': 'API duplex', 'slug': 'duplex'},
            ],
          }
        : schedule;
    return Success(BaseModel<T>(key: '', msg: '', data: params.mapper!(json)));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
