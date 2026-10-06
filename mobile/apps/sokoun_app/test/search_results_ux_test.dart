import 'dart:async';
import 'dart:convert';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/property_search_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

Map<String, dynamic> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  late _SearchSource search;
  late _OptionsRepository options;

  setUpAll(() async {
    messenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/shared_preferences'),
      (call) async => call.method == 'getAll' ? <String, Object>{} : true,
    );
    messenger.setMockMethodCallHandler(
      const MethodChannel('dev.fluttercommunity.plus/connectivity'),
      (_) async => ['wifi'],
    );
    await EasyLocalization.ensureInitialized();
    _translations =
        jsonDecode(
              await rootBundle.loadString(
                'packages/melos_core/assets/translations/en.json',
              ),
            )
            as Map<String, dynamic>;
    await CacheStorage.init();
  });
  setUp(() async {
    await injector.reset();
    search = _SearchSource();
    options = _OptionsRepository();
    injector.registerSingleton<PropertySearchDataSource>(search);
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: options),
    );
  });
  tearDown(() async => injector.reset());

  Future<void> pumpSearch(WidgetTester tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: const [Locale('en')],
        path: 'unused',
        assetLoader: const _Translations(),
        startLocale: const Locale('en'),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            navigatorObservers: [AppNavigationObserver.instance],
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: TenantSearchResultsScreen(
              initialFilters: PropertySearchFilters.initial().copyWith(
                search: 'Original query',
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
  }

  testWidgets(
    'listings load while metadata is pending and remain during replacement',
    (tester) async {
      await pumpSearch(tester);
      expect(search.requests, hasLength(1));
      expect(options.request.isCompleted, isFalse);
      search.complete(['Previous property']);
      await tester.pumpAndSettle();
      expect(find.text('Previous property'), findsOneWidget);
      await tester.enterText(find.byType(TextField), 'New query');
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));
      expect(search.filters.last.search, 'New query');
      expect(find.text('Previous property'), findsOneWidget);
      expect(
        find.text(LocaleKeys.searchUpdatingPreviousResults),
        findsOneWidget,
      );
      search.complete(['New property']);
      await tester.pumpAndSettle();
      expect(find.text('Previous property'), findsNothing);
      expect(find.text('New property'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets(
    'Back to search restores the same query, results and scroll position',
    (tester) async {
      await pumpSearch(tester);
      search.complete(List.generate(20, (index) => 'Property $index'));
      await tester.pumpAndSettle();
      final collection = find.byType(AppPagify<PropertyDetailsModel>);
      final position = tester
          .state<ScrollableState>(
            find
                .descendant(of: collection, matching: find.byType(Scrollable))
                .first,
          )
          .position;
      await tester.drag(collection, const Offset(0, -450));
      await tester.pumpAndSettle();
      final offset = position.pixels;
      expect(offset, greaterThan(0));
      unawaited(Go.to(const Scaffold()));
      await tester.pumpAndSettle();
      unawaited(
        Go.to(
          const VisitConfirmedScreen(
            property: VisitPropertyContent(
              id: 'property',
              ownerId: 'owner',
              title: 'Property',
              meta: '',
            ),
            selectedDay: VisitDayContent(
              weekday: 'saturday',
              day: '3',
              month: '10',
              visitDate: '2026-10-03',
            ),
            selectedTime: VisitTimeSlotContent(
              label: '2:00 PM',
              visitTime: '14:00',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text(LocaleKeys.tenantVisitBackToSearch));
      await tester.tap(find.text(LocaleKeys.tenantVisitBackToSearch));
      await tester.pumpAndSettle();
      expect(find.byType(TenantSearchResultsScreen), findsOneWidget);
      expect(find.byType(VisitConfirmedScreen), findsNothing);
      expect(position.pixels, closeTo(offset, .1));
      expect(search.requests, hasLength(1));
      expect(
        tester
            .widget<AppPagify<PropertyDetailsModel>>(collection)
            .pagifyController
            .items,
        hasLength(20),
      );
      expect(
        tester.widget<TextField>(find.byType(TextField)).controller!.text,
        'Original query',
      );
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}

class _SearchSource implements PropertySearchDataSource {
  final filters = <PropertySearchFilters>[];
  final requests = <Completer<(PropertySearchResponseModel, PaginationData)>>[];

  void complete(List<String> titles) => requests.last.complete((
    PropertySearchResponseModel.fromJson({
      'count': titles.length,
      'results': [
        for (final title in titles)
          {'id': title, 'title': title, 'price': '1200'},
      ],
    }),
    PaginationData(perPage: 20, totalPages: 1),
  ));

  @override
  String cacheKeyFor(PropertySearchFilters filters) => filters.cacheKey;

  @override
  Future<(PropertySearchResponseModel, PaginationData)> getPropertiesPage(
    PropertySearchFilters filter, {
    CancelToken? cancelToken,
  }) {
    filters.add(filter);
    final request = Completer<(PropertySearchResponseModel, PaginationData)>();
    requests.add(request);
    return request.future;
  }
}

class _OptionsRepository implements BaseRepository {
  final request = Completer<Map<String, dynamic>>();

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async => Success(
    BaseModel<T>(key: '', msg: '', data: params.mapper!(await request.future)),
  );

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations;
}
