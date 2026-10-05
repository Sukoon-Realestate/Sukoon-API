import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/time_zone_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_chip_wrap.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

import 'helpers/account_test_dependencies.dart';

// These fixtures are copied from MOBILE_DEV_HANDOFF.md, including decimal money,
// nullable dates, sparse availability, and the three verification flags.
final _fixtures =
    jsonDecode(
          File(
            'test/helpers/mobile_dev_handoff_fixtures.json',
          ).readAsStringSync(),
        )
        as Map<String, dynamic>;
Map<String, dynamic> _data(String key) =>
    Map<String, dynamic>.from(_fixtures[key]['data'] as Map);

const _user = UserModel(
  id: 'owner-1',
  name: 'سامي يوسف',
  phone: '01012345432',
  email: 'sami@example.com',
  type: 'owner',
);
final _property = OwnerPropertyContent.initial().copyWith(
  id: 'property-1',
  title: 'شقة مدينة نصر',
);
final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Repository repository;
  late _CityNetwork network;

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
    network = _CityNetwork();
    injector
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      )
      ..registerSingleton<NetworkService>(network);
  });
  tearDown(() => injector.reset());

  Future<void> pump(
    WidgetTester tester,
    Widget child, {
    String language = 'en',
    double width = 390,
    double scale = 1,
  }) async {
    tester.view.physicalSize = Size(width, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      EasyLocalization(
        key: ValueKey('$language-$width-$scale'),
        supportedLocales: const [Locale('en'), Locale('ar')],
        startLocale: Locale(language),
        fallbackLocale: const Locale('en'),
        saveLocale: false,
        path: 'unused',
        assetLoader: const _Translations(),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          minTextAdapt: true,
          splitScreenMode: true,
          enableScaleWH: () => false,
          enableScaleText: () => false,
          fontSizeResolver: (size, _) => size.toDouble(),
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            theme: SokounTheme.light,
            locale: context.locale,
            supportedLocales: context.supportedLocales,
            localizationsDelegates: context.localizationDelegates,
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: TextScaler.linear(scale)),
              child: child!,
            ),
            home: RepaintBoundary(
              key: const ValueKey('handoff-preview'),
              child: child,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  test(
    'profile city and email survive cache serialization; null stays unset',
    () {
      final profile = UserProfileContent.fromJson(_data('profile'));
      expect(profile.city?.name, 'الإسكندرية');
      expect(profile.city?.slug, 'alexandria');
      expect(profile.email, 'sami@example.com');
      expect(UserProfileContent.fromJson(profile.toJson()), profile);
      expect(UserProfileContent.fromJson({'city': null}).city, isNull);
    },
  );

  test(
    'profile PATCH preserves, replaces, or explicitly clears city',
    () async {
      const initial = ProfileEditBody.initial();
      expect(initial.toJson(), isNot(contains('city_id')));
      expect(initial.toUserJson(), isNot(contains('city_id')));
      final id = _data('profile')['city']['id'] as String;
      final changed = initial.copyWith(cityId: id, updateCity: true);
      expect(changed.toJson()['city_id'], id);
      expect(changed.toUserJson()['city_id'], id);
      final cleared = changed.copyWith(clearCity: true);
      expect(cleared.toJson()['city_id'], '');
      expect(cleared.toUserJson()['city_id'], '');
      final cubit = ProfileEditCubit();
      addTearDown(cubit.close);
      await cubit.editProfile(body: cleared, onSuccess: () {});
      expect(repository.requests.single.api, ApiConstants.editProfile);
      expect(repository.requests.single.httpRequestType, HttpRequestType.patch);
      expect(repository.requests.single.body?['city_id'], '');
    },
  );

  for (final isOwner in [true, false]) {
    testWidgets('profile city can be chosen and cleared (owner: $isOwner)', (
      tester,
    ) async {
      await registerAuthenticatedTestAccount(user: _user);
      await pump(
        tester,
        ProfileEditScreen(
          initialValue: _user,
          workspace: isOwner ? AppWorkspace.owner : AppWorkspace.tenant,
        ),
      );
      final selector = find.byType(ProfileCitySelector);
      await tester.ensureVisible(selector);
      await tester.pumpAndSettle();
      expect(
        tester.widget<ProfileCitySelector>(selector).city?.name,
        'الإسكندرية',
      );
      await tester.tap(
        find.descendant(of: selector, matching: find.byType(OutlinedButton)),
      );
      await tester.pumpAndSettle();
      expect(network.requests.single.path, ApiConstants.propertyCities);
      expect(network.requests.single.queryParameters, {
        'page': 1,
        'page_size': 10,
      });
      await tester.tap(find.text('API Cairo'));
      await tester.pumpAndSettle();
      expect(
        tester.widget<ProfileCitySelector>(selector).city?.id,
        'city-cairo',
      );
      await tester.tap(
        find.descendant(of: selector, matching: find.byType(OutlinedButton)),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Clear city'));
      await tester.pumpAndSettle();
      expect(tester.widget<ProfileCitySelector>(selector).city, isNull);
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();
      final request = repository.requests.last;
      expect(request.httpRequestType, HttpRequestType.patch);
      expect(request.body?['city_id'], '');
      expect(tester.takeException(), isNull);
    });
  }

  test('verification badges use independent flags from the handoff', () {
    final json = _data('property');
    final property = PropertyDetailsModel.fromJson(json);
    expect(property.isVerified, isTrue);
    expect(property.isOwnerVerified, isTrue);
    expect(property.isOwnershipVerified, isTrue);
    json['is_verified'] = false;
    json['owner']['is_verified'] = false;
    final unverified = PropertyDetailsModel.fromJson(json);
    expect(unverified.isVerified, isFalse);
    expect(unverified.isOwnerVerified, isFalse);
    expect(unverified.isOwnershipVerified, isTrue);
  });

  test('availability uses Cairo weeks across midnight and daylight saving', () {
    final summer = TimeZoneHelper.inLocation(
      'Africa/Cairo',
      instant: DateTime.utc(2026, 10, 4, 21, 30),
    );
    expect(summer.timeZoneOffset, const Duration(hours: 3));
    expect(summer.day, 5);
    expect(
      OwnerAvailabilityScheduleContent.startOfWeek(summer),
      DateTime(2026, 10, 5),
    );
    final winter = TimeZoneHelper.inLocation(
      'Africa/Cairo',
      instant: DateTime.utc(2026, 12, 6, 21, 30),
    );
    expect(winter.timeZoneOffset, const Duration(hours: 2));
    expect(winter.day, 6);
    expect(
      OwnerAvailabilityScheduleContent.startOfWeek(winter),
      DateTime(2026, 11, 30),
    );
    final transitionWeek = OwnerAvailabilityScheduleContent.fromJson({
      'week_start': '2026-10-26',
      'week_end': '2026-11-01',
      'days': [],
    }).withEditableDays();
    expect(transitionWeek.days, hasLength(7));
    expect(transitionWeek.days.last.date, '2026-11-01');
    expect(transitionWeek.days.every((day) => day.slots.isEmpty), isTrue);
  });

  test(
    'editing preserves backend tenant categories, weekly rent, and meters',
    () {
      final property = PropertyDetailsModel.fromJson({
        ..._data('property'),
        'bedrooms': 2,
        'bathrooms': 1,
        'area': 90,
        'floor': 3,
        'rental_period': 6,
        'price_period': 'weekly',
        'suitable_for': 'female_students',
        'amenities': ['wifi', 'electricity_meter', 'water_meter'],
      });
      final form = OwnerAddPropertyMapper.fromProperty(property).form;
      final body = form.toJson();
      expect(body['price_period'], 'weekly');
      expect(body['suitable_for'], 'female_students');
      expect(body['has_electricity_meter'], isTrue);
      expect(body['has_water_meter'], isTrue);
      expect(
        form.amenityApiValues,
        containsAll(['wifi', 'electricity_meter', 'water_meter']),
      );
    },
  );

  testWidgets('statistics load from API and period selection refetches', (
    tester,
  ) async {
    await pump(tester, OwnerPropertyAnalyticsScreen(property: _property));
    expect(repository.requests.single.api, 'properties/property-1/statistics/');
    expect(repository.requests.single.queryParameters, {'period': '30_days'});
    expect(find.text('142'), findsOneWidget);
    expect(find.text('95%'), findsOneWidget);
    final chart = tester.widget<OwnerAnalyticsBarChart>(
      find.byType(OwnerAnalyticsBarChart),
    );
    expect(chart.values, [12, 15, 8]);
    expect(chart.dates, ['2026-09-18', '2026-09-19', '2026-09-20']);
    await tester.drag(find.byType(ListView), const Offset(0, -550));
    await tester.pumpAndSettle();
    final interests = tester.widget<OwnerPropertyInterestCard>(
      find.byType(OwnerPropertyInterestCard),
    );
    expect(interests.items.map((item) => item.value), [85, 70, 60]);
    final dropdown = tester.widget<DropdownButtonFormField<String>>(
      find.byType(DropdownButtonFormField<String>),
    );
    dropdown.onChanged!('7_days');
    await tester.pumpAndSettle();
    expect(repository.requests.last.queryParameters, {'period': '7_days'});
    expect(
      repository.requests.last.cacheKey,
      'owner_statistics_property-1_7_days',
    );
    final request =
        repository.requests.last
            as CrudBaseParmas<OwnerPropertyAnalyticsContent>;
    final model = OwnerPropertyAnalyticsContent.fromJson(_data('analytics'));
    expect(request.fromCacheJson!(request.toJson!(model)), model);
    expect(tester.takeException(), isNull);
  });

  test('a slower analytics request cannot overwrite the new period', () async {
    repository.delayAnalytics = true;
    final cubit = OwnerPropertyAnalyticsCubit();
    addTearDown(cubit.close);
    final old = cubit.load(propertyId: 'property-1', period: '30_days');
    final recent = cubit.load(propertyId: 'property-1', period: '7_days');
    repository.analyticsResponses.last.complete({
      ..._data('analytics'),
      'period': '7_days',
      'views_count': 7,
    });
    await recent;
    repository.analyticsResponses.first.complete(_data('analytics'));
    await old;
    expect(cubit.data.period, '7_days');
    expect(cubit.data.views, 7);
    expect(repository.requests.first.cancelToken?.isCancelled, isTrue);
  });

  testWidgets(
    'revenue uses backend amounts and statuses with Egyptian pounds',
    (tester) async {
      await pump(tester, const OwnerRevenueScreen());
      expect(repository.requests.single.api, ApiConstants.ownerRevenues);
      expect(find.text('36,000 EGP'), findsOneWidget);
      expect(find.text('+8% عن الشهر السابق'), findsOneWidget);
      expect(find.text('قادم 15 أكتوبر'), findsOneWidget);
      expect(find.text('+12,000 EGP'), findsOneWidget);
      final model = OwnerRevenueContent.fromJson(_data('revenue'));
      expect(model.properties.last.status, OwnerRevenueStatus.upcoming);
      expect(model.properties.first.dueDate, '');
      final request =
          repository.requests.single as CrudBaseParmas<OwnerRevenueContent>;
      expect(request.fromCacheJson!(request.toJson!(model)), model);
      final debit = OwnerTransactionContent.fromJson({
        'amount': 125.75,
        'currency': 'EGP',
        'is_credit': false,
      });
      expect(debit.amountLabel, '125.75');
      expect(debit.isCredit, isFalse);
      expect(OwnerTransactionContent.fromJson(debit.toJson()), debit);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'empty revenue retains real totals and has a contextual empty state',
    (tester) async {
      repository.revenue = {'total_this_month': 0, 'currency': 'EGP'};
      await pump(tester, const OwnerRevenueScreen());
      expect(find.byType(OwnerRevenueEmptyState), findsOneWidget);
      expect(find.text('0 EGP'), findsOneWidget);
      expect(find.byType(OwnerRevenuePropertyCard), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('failed revenue loads offer retry and recover', (tester) async {
    repository.fail = true;
    await pump(tester, const OwnerRevenueScreen());
    expect(find.byType(ExceptionView), findsOneWidget);
    repository.fail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(repository.requests, hasLength(2));
    expect(find.byType(OwnerRevenueContentView), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('empty days accept new times without inventing initial slots', (
    tester,
  ) async {
    await pump(
      tester,
      OwnerAvailabilityScreen(
        ownerPropertyId: 'property-1',
        availabilityStartDate: DateTime(2026, 10, 5),
      ),
    );
    expect(repository.requests.single.queryParameters, {
      'week_start': '2026-10-05',
    });
    final content = tester.widget<OwnerAvailabilityContent>(
      find.byType(OwnerAvailabilityContent),
    );
    expect(content.days, hasLength(7));
    expect(content.slots, isEmpty);
    content.onAddTimePressed!();
    await tester.pumpAndSettle();
    expect(find.byType(TimePickerDialog), findsOneWidget);
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    final updated = tester.widget<OwnerAvailabilityContent>(
      find.byType(OwnerAvailabilityContent),
    );
    expect(updated.slots.single.time, '12:00:00');
    await updated.onSavePressed();
    expect(repository.requests.last.body, {
      'availability_date': '2026-10-05',
      'slots': [
        {'time': '12:00:00', 'is_enabled': true},
      ],
    });
    expect(tester.takeException(), isNull);
  });

  testWidgets('week changes retain drafts and save all edited dates', (
    tester,
  ) async {
    await pump(
      tester,
      OwnerAvailabilityScreen(
        ownerPropertyId: 'property-1',
        availabilityStartDate: DateTime(2026, 10, 6),
      ),
    );
    OwnerAvailabilityContent content() =>
        tester.widget<OwnerAvailabilityContent>(
          find.byType(OwnerAvailabilityContent),
        );
    content().onTimePressed(0);
    await tester.pump();
    content().onNextWeek!();
    await tester.pumpAndSettle();
    expect(repository.requests.last.queryParameters, {
      'week_start': '2026-10-12',
    });
    content().onDaySelected(1);
    await tester.pump();
    content().onTimePressed(1);
    await tester.pump();
    await content().onSavePressed();
    final puts = repository.requests
        .where((request) => request.httpRequestType == HttpRequestType.put)
        .toList();
    expect(puts.map((request) => request.body?['availability_date']), [
      '2026-10-06',
      '2026-10-13',
    ]);
    expect(puts.first.body?['slots'], [
      {'time': '10:00:00', 'is_enabled': false},
      {'time': '14:00:00', 'is_enabled': true},
    ]);
    expect(tester.takeException(), isNull);
  });

  testWidgets('booking conflicts retain the edited slots for retry', (
    tester,
  ) async {
    repository.rejectAvailability = true;
    await pump(
      tester,
      OwnerAvailabilityScreen(
        ownerPropertyId: 'property-1',
        availabilityStartDate: DateTime(2026, 10, 6),
      ),
    );
    OwnerAvailabilityContent content() =>
        tester.widget<OwnerAvailabilityContent>(
          find.byType(OwnerAvailabilityContent),
        );
    content().onTimePressed(0);
    await tester.pump();
    await content().onSavePressed();
    await tester.pump();
    expect(content().slots.first.isEnabled, isFalse);
    expect(content().isSaving, isFalse);
    expect(find.byType(OwnerAvailabilityScreen), findsOneWidget);
    repository.rejectAvailability = false;
    await content().onSavePressed();
    await tester.pumpAndSettle();
    expect(
      repository.requests.where(
        (request) => request.httpRequestType == HttpRequestType.put,
      ),
      hasLength(2),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'partial multi-day saves retain successful changes and retry only failures',
    (tester) async {
      repository.rejectAvailabilityDate = '2026-10-05';
      await pump(
        tester,
        OwnerAvailabilityScreen(
          ownerPropertyId: 'property-1',
          availabilityStartDate: DateTime(2026, 10, 6),
        ),
      );
      OwnerAvailabilityContent content() =>
          tester.widget<OwnerAvailabilityContent>(
            find.byType(OwnerAvailabilityContent),
          );
      content().onTimePressed(0);
      await tester.pump();
      content().onDaySelected(0);
      await tester.pump();
      content().onAddTimePressed!();
      await tester.pumpAndSettle();
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();
      await content().onSavePressed();
      await tester.pumpAndSettle();
      content().onDaySelected(1);
      await tester.pump();
      expect(content().slots.first.isEnabled, isFalse);
      content().onDaySelected(2);
      await tester.pump();
      expect(content().slots, isEmpty);
      expect(content().canSave, isTrue);
      repository.rejectAvailabilityDate = null;
      await content().onSavePressed();
      await tester.pumpAndSettle();
      final puts = repository.requests
          .where((request) => request.httpRequestType == HttpRequestType.put)
          .toList();
      expect(puts.map((request) => request.body?['availability_date']), [
        '2026-10-06',
        '2026-10-05',
        '2026-10-05',
      ]);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('owner Profile opens API-backed revenue', (tester) async {
    await registerAuthenticatedTestAccount(user: _user);
    await pump(
      tester,
      const ProfileScreen(workspace: AppWorkspace.owner, user: _user),
    );
    await tester.ensureVisible(find.text('Revenue'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Revenue'));
    await tester.pumpAndSettle();
    expect(find.byType(OwnerRevenueScreen), findsOneWidget);
    expect(repository.requests.first.api, ApiConstants.ownerProfile);
    expect(repository.requests.last.api, ApiConstants.ownerRevenues);
    expect(tester.takeException(), isNull);
  });

  testWidgets('owned property analytics opens the real endpoint', (
    tester,
  ) async {
    await pump(
      tester,
      AppScaffold(
        body: ListView(
          children: [
            OwnerPropertyCard(
              property: _property,
              onEditPressed: () {},
              onRejectedPressed: () {},
              onDeletePressed: () {},
            ),
          ],
        ),
      ),
    );
    await tester.tap(find.text('Property analytics'));
    await tester.pumpAndSettle();
    expect(find.byType(OwnerPropertyAnalyticsScreen), findsOneWidget);
    expect(
      repository.requests.last.api,
      ApiConstants.propertyStatistics('property-1'),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('pricing uses API option labels and sends API values', (
    tester,
  ) async {
    OwnerAddPropertyFormState form = OwnerAddPropertyFormState.initial()
        .copyWith(
          bedrooms: '2',
          bathrooms: '1',
          space: '90',
          floor: '3',
          rentalDuration: '6',
        );
    final price = TextEditingController(),
        duration = TextEditingController(),
        description = TextEditingController();
    addTearDown(() {
      price.dispose();
      duration.dispose();
      description.dispose();
    });
    await pump(
      tester,
      AppScaffold(
        body: AddPropertyPricingPage(
          form: form,
          monthlyPriceController: price,
          rentalDurationController: duration,
          descriptionController: description,
          onMonthlyPriceChanged: (_) {},
          onSuitableForSelected: (value) =>
              form = form.copyWith(suitableFor: value),
          onRentalDurationChanged: (_) {},
          onRentalUnitChanged: (value) =>
              form = form.copyWith(rentalUnit: value),
          onAmenityToggled: (value) => form = form.copyWith(amenities: {value}),
          onDescriptionChanged: (_) {},
          onAdditionalDetailsChanged: (value) => form = value,
          onOptionLabelsLoaded: (labels) =>
              form = form.copyWith(optionLabels: labels),
          onNext: () {},
        ),
      ),
    );
    expect(repository.requests.single.api, ApiConstants.propertyFilterOptions);
    expect(find.text('EGP'), findsOneWidget);
    final wraps = tester
        .widgetList<AddPropertyChipWrap>(find.byType(AddPropertyChipWrap))
        .toList();
    expect(
      wraps.first.chips.map((chip) => chip.label),
      contains('API electricity'),
    );
    final meter = wraps.first.chips.firstWhere(
      (chip) => chip.selectionValue == 'electricity_meter',
    );
    wraps.first.onChipTap!(meter);
    final residents = wraps.firstWhere(
      (wrap) => wrap.chips.any((chip) => chip.selectionValue == 'students'),
    );
    residents.onChipTap!(residents.chips.single);
    expect(form.toJson()['has_electricity_meter'], isTrue);
    expect(form.toJson()['suitable_for'], 'students');
    tester
        .widget<AddPropertyPricingPage>(find.byType(AddPropertyPricingPage))
        .onRentalUnitChanged('weekly');
    expect(form.toJson()['price_period'], 'weekly');
    expect(form.rentalUnitLabel, 'API weekly');
    expect(form.suitableForLabel, 'API students');
    expect(form.amenityLabels, ['API electricity']);
    expect(form.toJson(), isNot(contains('option_labels')));
    expect(tester.takeException(), isNull);
  });

  Future<void> capture(
    WidgetTester tester,
    String subject,
    String language,
    double width,
    double scale,
  ) async {
    final output = Platform.environment['HANDOFF_CAPTURE_DIR'] ?? '';
    if (output.isEmpty || scale != 1 || (width != 390 && width != 1024)) return;
    final RenderRepaintBoundary boundary = tester.renderObject(
      find.byKey(const ValueKey('handoff-preview')),
    );
    await tester.runAsync(() async {
      final image = await boundary.toImage();
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      await Directory(output).create(recursive: true);
      await File(
        '$output/$subject-$language-$width.png',
      ).writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  }

  // All new information surfaces must remain usable in both reading directions
  // at the repository's supported phone/tablet/desktop widths and text scales.
  for (final language in ['en', 'ar']) {
    for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
      for (final scale in [1.0, 1.3, 2.0]) {
        testWidgets('handoff layouts $language width=$width scale=$scale', (
          tester,
        ) async {
          await pump(
            tester,
            OwnerPropertyAnalyticsScreen(property: _property),
            language: language,
            width: width,
            scale: scale,
          );
          expect(tester.takeException(), isNull);
          await capture(tester, 'analytics', language, width, scale);
          await tester.drag(find.byType(ListView), const Offset(0, -750));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          await pump(
            tester,
            const OwnerRevenueScreen(),
            language: language,
            width: width,
            scale: scale,
          );
          expect(tester.takeException(), isNull);
          await capture(tester, 'revenue', language, width, scale);
          await tester.drag(find.byType(ListView), const Offset(0, -750));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          await pump(
            tester,
            OwnerAvailabilityScreen(
              ownerPropertyId: 'property-1',
              availabilityStartDate: DateTime(2026, 10, 6),
            ),
            language: language,
            width: width,
            scale: scale,
          );
          expect(tester.takeException(), isNull);
          await capture(tester, 'availability', language, width, scale);
          await tester.drag(
            find.byType(SingleChildScrollView).first,
            const Offset(0, -750),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
}

class _Repository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  final List<Completer<Map<String, dynamic>>> analyticsResponses = [];
  bool fail = false, delayAnalytics = false, rejectAvailability = false;
  String? rejectAvailabilityDate;
  Map<String, dynamic> revenue = _data('revenue');

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    if (fail) return const Error(Failure('Request failed'));
    if ((rejectAvailability ||
            (rejectAvailabilityDate != null &&
                params.body?['availability_date'] == rejectAvailabilityDate)) &&
        params.httpRequestType == HttpRequestType.put) {
      return const Error(Failure('Booked visit slots cannot be disabled.'));
    }
    Map<String, dynamic> json;
    if (params.api.endsWith('/statistics/')) {
      if (delayAnalytics) {
        final gate = Completer<Map<String, dynamic>>();
        analyticsResponses.add(gate);
        json = await gate.future;
      } else {
        json = {
          ..._data('analytics'),
          'period': params.queryParameters?['period'],
        };
      }
    } else if (params.api == ApiConstants.ownerRevenues) {
      json = revenue;
    } else if (params.api == ApiConstants.userProfile) {
      json = {..._data('profile'), 'avatar': ''};
    } else if (params.api == ApiConstants.propertyFilterOptions) {
      json = {
        'price_periods': [
          {'value': 'weekly', 'label': 'API weekly'},
        ],
        'suitable_for': [
          {'value': 'students', 'label': 'API students'},
        ],
        'amenities': [
          {
            'value': 'electricity_meter',
            'label': 'API electricity',
            'query_parameter': 'has_electricity_meter',
          },
        ],
      };
    } else if (params.api.endsWith('/availability/')) {
      json = _data('availability');
      if (params.httpRequestType == HttpRequestType.get) {
        final start = DateTime.parse(
          params.queryParameters!['week_start'] as String,
        );
        final savedDay = DateTime(start.year, start.month, start.day + 1);
        json['week_start'] = OwnerVisitCalendarContent.formatDate(start);
        json['week_end'] = OwnerVisitCalendarContent.formatDate(
          DateTime(start.year, start.month, start.day + 6),
        );
        json['days'] = [
          {
            ...Map<String, dynamic>.from((json['days'] as List).single as Map),
            'date': OwnerVisitCalendarContent.formatDate(savedDay),
          },
        ];
      }
    } else {
      json = {};
    }
    return Success(BaseModel<T>(key: '', msg: '', data: params.mapper!(json)));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _CityNetwork implements NetworkService {
  final List<NetworkRequest> requests = [];
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) async {
    requests.add(request);
    return BaseModel<T>(
      key: '',
      msg: '',
      data: mapper!({
        'count': 1,
        'next': null,
        'results': [
          {'id': 'city-cairo', 'name': 'API Cairo', 'slug': 'cairo'},
        ],
      }),
    );
  }

  @override
  Future<bool> hasSessionCookies() async => true;
  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<void> updateBaseUrl() async {}
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations[locale.languageCode]!;
}
