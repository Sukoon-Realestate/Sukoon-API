import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  const preferences = MethodChannel('plugins.flutter.io/shared_preferences');
  const connectivity = MethodChannel('dev.fluttercommunity.plus/connectivity');
  const connectivityStatus = MethodChannel(
    'dev.fluttercommunity.plus/connectivity_status',
  );
  late _PropertiesNetwork network;

  setUpAll(() async {
    messenger.setMockMethodCallHandler(
      preferences,
      (call) async => call.method == 'getAll' ? <String, Object>{} : true,
    );
    messenger.setMockMethodCallHandler(connectivity, (_) async => ['wifi']);
    messenger.setMockMethodCallHandler(connectivityStatus, (_) async => null);
    await EasyLocalization.ensureInitialized();
    await _Translations.preload();
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
    network = _PropertiesNetwork();
    injector.registerSingleton<NetworkService>(network);
  });

  tearDown(() => injector.reset());
  tearDownAll(() {
    messenger.setMockMethodCallHandler(preferences, null);
    messenger.setMockMethodCallHandler(connectivity, null);
    messenger.setMockMethodCallHandler(connectivityStatus, null);
  });

  test('maps the supplied listing and preserves authoritative pagination', () {
    final response = OwnerPropertiesResponse.fromJson({
      'per_page': 7,
      'total_pages': 4,
      'count': 21,
      'results': [
        {
          'id': '13954644-cc37-49d9-a772-f1a88be81401',
          'title': 'saudi arabia',
          'main_image': 'https://example.com/property.jpg',
          'price': '60000000.00',
          'price_period': 'weekly',
          'status': 'under_review',
          'is_verified': false,
          'views_count': 2,
          'visits_count': 0,
        },
      ],
    });
    expect(response.perPage, 7);
    expect(response.totalPages, 4);
    expect(response.count, 21);
    expect(response.results.single.status.isPending, isTrue);
    expect(response.results.single.monthlyPrice, 60000000);
    expect(response.results.single.pricePeriod, 'weekly');
    expect(response.results.single.views, 2);
    expect(response.results.single.visitRequests, 0);
    expect(OwnerPropertiesResponse.fromJson(response.toJson()), response);
  });

  test('accepted review status is independent of verification', () {
    final property = OwnerPropertyContent.fromJson({
      'id': 'accepted-property',
      'status': 'accepted',
      'is_verified': false,
    });
    expect(property.status.isAccepted, isTrue);
    expect(property.status.isVerified, isFalse);
    expect(OwnerPropertyFilter.accepted.accepts(property.status), isTrue);
    expect(OwnerPropertyFilter.underReview.accepts(property.status), isFalse);
  });

  test('supports legacy pagination and empty responses', () {
    final legacy = OwnerPropertiesResponse.fromJson({
      'count': 25,
      'results': [],
    });
    expect(legacy.perPage, 10);
    expect(legacy.totalPages, 3);
    final empty = OwnerPropertiesResponse.fromJson({
      'count': 0,
      'per_page': 10,
      'total_pages': 0,
      'results': [],
    });
    expect(empty.totalPages, 1);
    expect(empty.results, isEmpty);
  });

  for (final filter in OwnerPropertyFilter.values) {
    test('requests ${filter.apiValue} with server pagination', () async {
      network.pagination = {'per_page': 7, 'total_pages': 4, 'count': 21};
      final (_, pagination) = await OwnerPropertiesData.getOwnedPropertiesPage(
        page: 3,
        filter: filter,
      );
      expect(network.requests.single.path, ApiConstants.ownedProperties);
      expect(network.requests.single.method, RequestMethod.get);
      expect(network.requests.single.queryParameters, {
        'page': 3,
        'page_size': 10,
        'status': filter.apiValue,
      });
      expect(pagination.perPage, 7);
      expect(pagination.totalPages, 4);
    });
  }

  testWidgets('tab selection resets pagination and keeps refresh scoped', (
    tester,
  ) async {
    await _mount(tester);
    await _selectTab(tester, OwnerPropertyFilter.accepted);
    final first = tester.widget<AppPagify<OwnerPropertyContent>>(
      find.byType(AppPagify<OwnerPropertyContent>),
    );
    await first.pagifyController.refresh();
    await tester.pumpAndSettle();
    await _selectTab(tester, OwnerPropertyFilter.accepted);
    expect(
      network.requests.map((request) => request.queryParameters?['status']),
      ['under_review', 'accepted', 'accepted'],
    );
    await _selectTab(tester, OwnerPropertyFilter.rejected);
    final second = tester.widget<AppPagify<OwnerPropertyContent>>(
      find.byType(AppPagify<OwnerPropertyContent>),
    );
    expect(second.pagifyController, isNot(same(first.pagifyController)));
    expect(second.cacheKey, 'owner_properties_rejected_all_en');
    expect(first.cacheKey, 'owner_properties_accepted_all_en');
    expect(network.requests.last.queryParameters?['page'], 1);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('an empty status retains tabs and an actionable empty state', (
    tester,
  ) async {
    network.emptyStatuses.add('rejected');
    await _mount(tester);
    await _selectTab(tester, OwnerPropertyFilter.rejected);
    expect(find.byType(OwnerPropertiesStatusTabs), findsOneWidget);
    expect(find.byType(OwnerPropertiesEmptyState), findsOneWidget);
    expect(find.text(OwnerPropertyFilter.rejected.emptyTitle), findsOneWidget);
    expect(find.byType(OwnerPropertyCard), findsNothing);
    expect(find.text('Add property'), findsOneWidget);
    await _capture(tester, 'listings-rejected-empty-en-390');
    await _selectTab(tester, OwnerPropertyFilter.underReview);
    expect(find.text('Property under_review'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets(
    'late results from the previous tab do not replace the selected list',
    (tester) async {
      final pending = Completer<Map<String, dynamic>>();
      network.pendingReview = pending;
      await _mount(tester, settle: false);
      expect(network.requests, hasLength(1));
      await _selectTab(tester, OwnerPropertyFilter.accepted);
      pending.complete(network.responseFor('under_review'));
      await tester.pumpAndSettle();
      expect(find.text('Property accepted'), findsOneWidget);
      expect(find.text('Property under_review'), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets('leaving listings ignores late request failures', (tester) async {
    final pending = Completer<Map<String, dynamic>>();
    network.pendingReview = pending;
    await _mount(tester, settle: false);
    await tester.pumpWidget(const SizedBox.shrink());
    pending.completeError(ServerException('Late listing failure'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  for (final locale in ['ar', 'en']) {
    for (final double width in [320, 390, 600, 768, 1024, 1366]) {
      for (final double scale in [1, 1.3, 2]) {
        testWidgets('listing tabs $locale width=$width text=$scale', (
          tester,
        ) async {
          await _mount(tester, locale: locale, width: width, scale: scale);
          for (final filter in OwnerPropertyFilter.values) {
            await _selectTab(tester, filter);
            final pagify = tester.widget<AppPagify<OwnerPropertyContent>>(
              find.byType(AppPagify<OwnerPropertyContent>),
            );
            expect(
              pagify.cacheKey,
              'owner_properties_${filter.apiValue}_all_$locale',
            );
            expect(find.text('Property ${filter.apiValue}'), findsOneWidget);
            expect(network.requests.last.queryParameters, {
              'page': 1,
              'page_size': 10,
              'status': filter.apiValue,
            });
            if (scale == 1 && (width == 390 || width == 1024)) {
              await _capture(
                tester,
                'listings-${filter.apiValue}-$locale-${width.toInt()}',
              );
            }
            expect(tester.takeException(), isNull);
          }
          expect(network.requests, hasLength(3));
          await tester.pumpWidget(const SizedBox.shrink());
        });
      }
    }
  }
}

Future<void> _mount(
  WidgetTester tester, {
  String locale = 'en',
  double width = 390,
  double scale = 1,
  bool settle = true,
}) async {
  tester.view.physicalSize = Size(width, width > 900 ? 768 : 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      path: 'unused',
      assetLoader: const _Translations(),
      startLocale: Locale(locale),
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
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: true,
            ),
            child: child!,
          ),
          home: const RepaintBoundary(child: OwnerListingsScreen()),
        ),
      ),
    ),
  );
  await tester.runAsync(() async => Future<void>.delayed(Duration.zero));
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Future<void> _selectTab(WidgetTester tester, OwnerPropertyFilter filter) async {
  final tab = find.descendant(
    of: find.byType(TabBar),
    matching: find.text(filter.label),
  );
  await tester.ensureVisible(tab);
  await tester.pump();
  await tester.tap(tab);
  await tester.pumpAndSettle();
}

Future<void> _capture(WidgetTester tester, String name) async {
  const output = String.fromEnvironment('UI_REVIEW_DIR');
  if (output.isEmpty) return;
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find
        .ancestor(
          of: find.byType(OwnerListingsScreen),
          matching: find.byType(RepaintBoundary),
        )
        .first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 1);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    final directory = Directory(output)..createSync(recursive: true);
    await File(
      '${directory.path}/$name.png',
    ).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

class _Translations extends AssetLoader {
  const _Translations();

  static final Map<String, Map<String, dynamic>> _values = {};

  static Future<void> preload() async {
    for (final locale in ['ar', 'en']) {
      _values[locale] = Map<String, dynamic>.from(
        jsonDecode(
              await rootBundle.loadString(
                'packages/melos_core/assets/translations/$locale.json',
              ),
            )
            as Map,
      );
    }
  }

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _values[locale.languageCode]!;
}

class _PropertiesNetwork implements NetworkService {
  final List<NetworkRequest> requests = [];
  final Set<String> emptyStatuses = {};
  Map<String, int> pagination = {'per_page': 10, 'total_pages': 1, 'count': 1};
  Completer<Map<String, dynamic>>? pendingReview;

  Map<String, dynamic> responseFor(String status) => {
    ...pagination,
    if (emptyStatuses.contains(status)) 'count': 0,
    'results': [
      if (!emptyStatuses.contains(status))
        {
          'id': 'property-$status',
          'title': 'Property $status',
          'main_image': '',
          'price': '60000000.00',
          'price_period': 'weekly',
          'status': status,
          'is_verified': false,
          'views_count': 2,
          'visits_count': 0,
        },
    ],
  };

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    requests.add(networkRequest);
    final String status = networkRequest.queryParameters!['status'] as String;
    final json = status == 'under_review' && pendingReview != null
        ? await pendingReview!.future
        : responseFor(status);
    return BaseModel<Model>(key: '', msg: '', data: mapper!(json));
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => false;

  @override
  Future<void> updateBaseUrl() async {}
}
