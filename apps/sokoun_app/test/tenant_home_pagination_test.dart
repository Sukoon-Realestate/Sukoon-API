import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/retry_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_home_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/imports.dart';
import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _HomeRepository repository;
  late TenantHomeData data;
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
  });
  setUp(() async {
    await injector.reset();
    AccountSession.end();
    repository = _HomeRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    registerHomePageTestDependencies();
    data = TenantHomeData();
  });
  tearDown(() async {
    await injector.reset();
    AccountSession.end();
  });

  test(
    'loads only when requested and preserves complete per-page cache contracts',
    () async {
      expect(repository.requests, isEmpty);
      final first = data.getPage(page: 1);
      final params = repository.requests.single.params;
      expect(params.queryParameters, {'page': 1});
      final model = HomePageModel.fromJson(
        _page(['first'], nextPage: 2, banner: 'visit'),
      );
      expect(params.fromCacheJson!(params.toJson!(model)), model);
      repository.requests.single.complete(model.toJson());
      final (loaded, pagination) = await first;
      expect(loaded.banner, 'visit');
      expect(pagination.totalPages, 2);
      final next = data.getPage(page: 2);
      expect(repository.requests.last.params.cacheKey, isNot(params.cacheKey));
      repository.requests.last.complete(_page(['second']));
      expect((await next).$2.totalPages, 2);
    },
  );

  test('uses server next links and resets them on refresh', () async {
    final first = data.getPage(page: 1);
    repository.requests.last.complete(_page(['one'], nextPage: 3));
    await first;
    final second = data.getPage(page: 2);
    expect(repository.requests.last.params.queryParameters, {'page': 3});
    repository.requests.last.complete(_page(['three']));
    await second;
    final refresh = data.getPage(page: 1);
    expect(repository.requests.last.params.queryParameters, {'page': 1});
    repository.requests.last.complete(_page(['fresh']));
    expect((await refresh).$1.results.single.id, 'fresh');
  });

  test(
    'failed pages surface an error and can retry the same server page',
    () async {
      final request = data.getPage(page: 1);
      repository.requests.last.fail('Unavailable');
      await expectLater(request, throwsA(isA<PagifyApiRequestException>()));
      final retry = data.getPage(page: 1);
      repository.requests.last.complete(_page(['restored']));
      expect((await retry).$1.results.single.id, 'restored');
    },
  );

  testWidgets(
    'empty success and errors retain search controls and expose retry',
    (tester) async {
      await _pumpHome(tester);
      repository.requests.last.fail(LocaleKeys.checkInternet);
      await tester.pumpAndSettle();
      expect(find.byType(AppRetryView), findsOneWidget);
      expect(find.byType(HomeSearchBox), findsOneWidget);
      await tester.tap(find.text(LocaleKeys.ownerRetryAction));
      await tester.pumpAndSettle();
      repository.requests.last.complete(_page([]));
      await tester.pumpAndSettle();
      expect(find.byType(TenantSuggestedPropertiesEmptyState), findsOneWidget);
      expect(find.byType(HomeSearchBox), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'loads the next page and resizing keeps items without a new request',
    (tester) async {
      await _pumpHome(tester);
      repository.requests.last.complete(
        _page(List.generate(20, (i) => 'item-$i'), nextPage: 2),
      );
      await tester.pumpAndSettle();
      final pagify = tester.widget<AppPagify<HomePropertyModel>>(
        find.byType(AppPagify<HomePropertyModel>),
      );
      final controller = pagify.pagifyController;
      expect(controller.items.length, 20);
      final scrollable = find
          .descendant(
            of: find.byType(AppPagify<HomePropertyModel>),
            matching: find.byType(Scrollable),
          )
          .first;
      final position = tester.state<ScrollableState>(scrollable).position;
      position.jumpTo(position.maxScrollExtent);
      await tester.pumpAndSettle();
      expect(repository.requests.length, 2);
      repository.requests.last.complete(_page(['last']));
      await tester.pumpAndSettle();
      expect(controller.items.length, 21);
      tester.view.physicalSize = const Size(1024, 768);
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<AppPagify<HomePropertyModel>>(
              find.byType(AppPagify<HomePropertyModel>),
            )
            .pagifyController,
        same(controller),
      );
      expect(repository.requests.length, 2);
      expect(controller.items.last.id, 'last');
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('refresh stays active until the replacement request finishes', (
    tester,
  ) async {
    await _pumpHome(tester);
    repository.requests.last.complete(_page(['old']));
    await tester.pumpAndSettle();
    bool completed = false;
    final refresh = tester
        .widget<RefreshIndicator>(find.byType(RefreshIndicator))
        .onRefresh()
        .then((_) => completed = true);
    await tester.pump();
    expect(completed, isFalse);
    repository.requests.last.complete(_page(['new']));
    await tester.pumpAndSettle();
    await refresh;
    final controller = tester
        .widget<AppPagify<HomePropertyModel>>(
          find.byType(AppPagify<HomePropertyModel>),
        )
        .pagifyController;
    expect(controller.items.single.id, 'new');
    expect(completed, isTrue);
  });

  testWidgets('disposed pages do not receive late responses', (tester) async {
    await _pumpHome(tester);
    final pending = repository.requests.last;
    await tester.pumpWidget(const SizedBox.shrink());
    pending.complete(_page(['old-account']));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}

Map<String, dynamic> _page(
  List<String> ids, {
  int? nextPage,
  String? banner,
}) => {
  'count': 4,
  'next': nextPage == null
      ? null
      : 'https://example.com/homepage?page=$nextPage',
  'results': [
    for (final id in ids) {'id': id, 'title': 'Property $id', 'price': '1200'},
  ],
  'banner': banner,
};

Future<void> _pumpHome(WidgetTester tester) async {
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
        enableScaleWH: () => false,
        enableScaleText: () => false,
        fontSizeResolver: (size, _) => size.toDouble(),
        builder: (context, _) => MaterialApp(
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
          home: MediaQuery(
            data: MediaQuery.of(context).copyWith(disableAnimations: true),
            child: const TenantHomeScreen(),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _HomeRepository implements BaseRepository {
  final List<_PageRequest> requests = [];

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    final request = _PageRequest(params as CrudBaseParmas<HomePageModel>);
    requests.add(request);
    final result = await request.response.future;
    return result.when(
      (json) =>
          Success(BaseModel<T>(key: '', msg: '', data: params.mapper!(json))),
      (failure) => Error(failure),
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _PageRequest {
  _PageRequest(this.params);

  final CrudBaseParmas<HomePageModel> params;
  final response = Completer<Result<Map<String, dynamic>, Failure>>();

  void complete(Map<String, dynamic> page) => response.complete(Success(page));
  void fail(String message) => response.complete(Error(ServerFailure(message)));
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    final file = [
      File('packages/core/assets/translations/en.json'),
      File('../../packages/core/assets/translations/en.json'),
    ].firstWhere((file) => file.existsSync());
    return jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  }
}
