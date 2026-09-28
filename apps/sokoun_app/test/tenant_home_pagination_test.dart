import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/cupertino.dart' show CupertinoActivityIndicator;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/widgets/custom_shimmer.dart';
import 'package:melos_core/core/widgets/retry_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/imports.dart';

import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  late _HomeRepository repository;
  late HomePageCubit cubit;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
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
    cubit = HomePageCubit();
  });

  tearDown(() async {
    await cubit.close();
    await injector.reset();
    AccountSession.end();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
  });

  Future<void> loadFirstPage() async {
    final request = cubit.getHomePage();
    repository.requests.last.complete(
      _page(['first'], nextPage: 2, banner: 'visit'),
    );
    await request;
  }

  test(
    'appends the next page, caches each page, and stops at the last page',
    () async {
      expect(repository.requests, isEmpty);
      expect(cubit.canLoadMore, isFalse);
      await loadFirstPage();
      expect(cubit.canLoadMore, isTrue);

      final request = cubit.loadMoreHomePage();
      expect(cubit.state.isLoadingMore, isTrue);
      expect(cubit.state.data.results.single.id, 'first');
      expect(cubit.canLoadMore, isFalse);
      await cubit.loadMoreHomePage();
      expect(repository.requests, hasLength(2));

      final pending = repository.requests.last;
      expect(pending.params.api, ApiConstants.homePage);
      expect(pending.params.httpRequestType, HttpRequestType.get);
      expect(pending.params.queryParameters, {'page': 2});
      expect(
        pending.params.cacheKey,
        isNot(repository.requests.first.params.cacheKey),
      );
      final HomePageModel page = HomePageModel.fromJson(_page(['second']));
      expect(pending.params.fromCacheJson!(pending.params.toJson!(page)), page);
      pending.complete(page.toJson());
      await request;

      expect(cubit.state.isSuccess, isTrue);
      expect(cubit.state.data.results.map((item) => item.id), [
        'first',
        'second',
      ]);
      expect(cubit.state.data.banner, 'visit');
      expect(cubit.state.data.next, isNull);
      expect(cubit.canLoadMore, isFalse);
      await cubit.loadMoreHomePage();
      expect(repository.requests, hasLength(2));
    },
  );

  test('uses the page number supplied by the next link', () async {
    final first = cubit.getHomePage();
    repository.requests.last.complete(_page(['first'], nextPage: 3));
    await first;
    final next = cubit.loadMoreHomePage();
    expect(repository.requests.last.params.queryParameters, {'page': 3});
    repository.requests.last.complete(_page(['third']));
    await next;
  });

  test('a failed next page keeps content and retries the same page', () async {
    await loadFirstPage();
    final request = cubit.loadMoreHomePage();
    repository.requests.last.fail('Page unavailable');
    await request;

    expect(cubit.state.isSuccess, isTrue);
    expect(cubit.state.msg, 'Page unavailable');
    expect(cubit.state.data.results.single.id, 'first');
    expect(cubit.canLoadMore, isTrue);

    final retry = cubit.loadMoreHomePage();
    expect(repository.requests.last.params.queryParameters, {'page': 2});
    repository.requests.last.complete(_page(['second']));
    await retry;
    expect(cubit.state.msg, isEmpty);
    expect(cubit.state.data.results, hasLength(2));
  });

  test(
    'refresh replaces all pages and ignores an older in-flight page',
    () async {
      await loadFirstPage();
      final loadMore = cubit.loadMoreHomePage();
      final oldPage = repository.requests.last;
      final refresh = cubit.getHomePage();
      expect(cubit.getHomePage(), same(refresh));
      expect(repository.requests.last.params.queryParameters, {'page': 1});
      repository.requests.last.complete(_page(['refreshed']));
      await refresh;
      oldPage.complete(_page(['stale'], nextPage: 3));
      await loadMore;

      expect(cubit.state.data.results.single.id, 'refreshed');
      expect(cubit.state.data.banner, isNull);
      expect(cubit.canLoadMore, isFalse);
      expect(repository.requests, hasLength(3));
    },
  );

  test('a first-page error can be retried', () async {
    final request = cubit.getHomePage();
    repository.requests.last.fail(LocaleKeys.checkInternet);
    await request;
    expect(cubit.state.isError, isTrue);
    expect(cubit.canLoadMore, isFalse);
    await loadFirstPage();
    expect(cubit.state.isSuccess, isTrue);
  });

  test('unexpected page errors also clear the loading-more state', () async {
    await loadFirstPage();
    final request = cubit.loadMoreHomePage();
    repository.requests.last.response.completeError(
      StateError('Unexpected error'),
    );
    await request;
    expect(cubit.state.isSuccess, isTrue);
    expect(cubit.state.msg, LocaleKeys.exceptionError);
    expect(cubit.canLoadMore, isTrue);
  });

  test(
    'late responses are ignored after disposal or an account change',
    () async {
      final request = cubit.getHomePage();
      await cubit.close();
      repository.requests.last.complete(_page(['disposed']));
      await request;
      expect(cubit.state.data.results, isEmpty);

      cubit = HomePageCubit();
      final nextRequest = cubit.getHomePage();
      AccountSession.begin('another-account');
      repository.requests.last.complete(_page(['previous-account']));
      await nextRequest;
      expect(cubit.state.data.results, isEmpty);
    },
  );

  testWidgets(
    'scrolling loads a page without replacing content or scroll position',
    (tester) async {
      await _pumpHome(tester);
      repository.requests.last.complete(
        _page(List.generate(10, (index) => 'property-$index'), nextPage: 2),
      );
      await tester.pumpAndSettle();

      final scrollView = tester.widget<SingleChildScrollView>(
        find.byType(SingleChildScrollView),
      );
      final controller = scrollView.controller!;
      controller.jumpTo(controller.position.maxScrollExtent - 100);
      final double offset = controller.offset;
      await tester.pump();

      expect(repository.requests, hasLength(2));
      expect(find.byType(TenantPropertyCard), findsNWidgets(10));
      expect(find.byType(SingleChildScrollView), findsOneWidget);
      expect(find.byType(CustomShimmer), findsNothing);
      expect(find.byType(CupertinoActivityIndicator), findsOneWidget);
      expect(controller.offset, offset);

      repository.requests.last.complete(_page(['four']));
      await tester.pumpAndSettle();
      expect(find.byType(TenantPropertyCard), findsNWidgets(11));
      expect(find.byType(CupertinoActivityIndicator), findsNothing);
      expect(controller.offset, offset);
      controller.jumpTo(controller.position.maxScrollExtent);
      await tester.pump();
      expect(repository.requests, hasLength(2));

      controller.jumpTo(0);
      await tester.pumpAndSettle();
      await tester.drag(
        find.byType(SingleChildScrollView),
        const Offset(0, 400),
      );
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));
      expect(repository.requests.last.params.queryParameters, {'page': 1});
      expect(repository.requests, hasLength(3));
      repository.requests.last.complete(_page(['refreshed']));
      await tester.pumpAndSettle();
      expect(find.byType(TenantPropertyCard), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets(
    'empty success retains home controls and offline errors offer retry',
    (tester) async {
      await _pumpHome(tester);
      repository.requests.last.fail(LocaleKeys.checkInternet);
      await tester.pumpAndSettle();
      expect(find.byType(AppRetryView), findsOneWidget);
      expect(find.byType(TenantSuggestedPropertiesEmptyState), findsNothing);

      await tester.tap(find.text(LocaleKeys.ownerRetryAction));
      await tester.pump();
      expect(repository.requests, hasLength(2));
      repository.requests.last.complete(_page([]));
      await tester.pumpAndSettle();
      expect(find.byType(TenantSuggestedPropertiesEmptyState), findsOneWidget);
      expect(find.byType(HomeSearchBox), findsOneWidget);
      expect(find.byType(TenantHeader), findsOneWidget);
      expect(find.byType(AppRetryView), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
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
