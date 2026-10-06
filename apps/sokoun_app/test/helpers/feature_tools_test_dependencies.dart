import 'dart:convert';
import 'dart:io';

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
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:toastification/toastification.dart';

class FeatureTestRequest {
  const FeatureTestRequest({
    required this.endpoint,
    required this.method,
    this.body,
    this.query,
    this.cacheKey,
    required this.hasSerializers,
  });
  final String endpoint;
  final HttpRequestType method;
  final dynamic body;
  final Map<String, dynamic>? query;
  final String? cacheKey;
  final bool hasSerializers;
}

class FeatureTestReply {
  const FeatureTestReply({
    this.data = const {},
    this.key = 'success',
    this.failure,
  });
  final Map<String, dynamic> data;
  final String key;
  final Failure? failure;
}

class FeatureTestRepository implements BaseRepository {
  final List<FeatureTestRequest> requests = [];
  final Map<String, FeatureTestReply> replies = {};
  Future<FeatureTestReply> Function(FeatureTestRequest)? handler;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    final request = FeatureTestRequest(
      endpoint: params.api,
      method: params.httpRequestType,
      body: params.body,
      query: params.queryParameters,
      cacheKey: params.cacheKey,
      hasSerializers: params.fromCacheJson != null && params.toJson != null,
    );
    requests.add(request);
    final reply = handler != null
        ? await handler!(request)
        : replies[request.endpoint] ?? defaultReply(request);
    if (reply.failure != null) return Error(reply.failure!);
    final mapped = params.mapper!(reply.data);
    return Success(BaseModel<T>(key: reply.key, msg: '', data: mapped));
  }

  FeatureTestReply defaultReply(FeatureTestRequest request) {
    final workspace = request.query?['workspace'] ?? 'owner';
    if (request.endpoint == PremiumApiConstants.configuration) {
      return FeatureTestReply(
        data: {
          'workspace': workspace,
          'alert_cadences': ['instant', 'daily'],
          'boost_options': [
            {'id': 'fixture-week', 'title': 'أسبوع', 'duration_days': 7},
          ],
        },
      );
    }
    return const FeatureTestReply();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class FeatureTestNetwork implements NetworkService {
  final List<NetworkRequest> requests = [];
  Map<String, dynamic> page = const {
    'results': [],
    'count': 0,
    'per_page': 20,
    'total_pages': 1,
  };
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest networkRequest, {
    T Function(dynamic)? mapper,
  }) async {
    requests.add(networkRequest);
    return BaseModel<T>(key: 'success', msg: '', data: mapper!(page));
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Future<void> initializeFeatureTestEnvironment() async {
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(
        const MethodChannel('plugins.flutter.io/shared_preferences'),
        (call) async => call.method == 'getAll' ? <String, Object>{} : true,
      );
  await EasyLocalization.ensureInitialized();
  await CacheStorage.init();
  for (final channel in [
    const MethodChannel('dev.fluttercommunity.plus/connectivity'),
    const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
  ]) {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          channel,
          (call) async => call.method == 'check' ? ['wifi'] : null,
        );
  }
}

Future<void> registerFeatureTestDependencies(
  FeatureTestRepository repository, {
  FeatureTestNetwork? network,
}) async {
  toastification.managers.clear();
  await injector.reset();
  injector.registerSingleton<BaseCrudUseCase>(
    BaseCrudUseCase(repository: repository),
  );
  injector.registerSingleton<NetworkService>(network ?? FeatureTestNetwork());
  AccountSession.begin('fixture-account');
}

class FeatureTestTranslations extends AssetLoader {
  const FeatureTestTranslations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}

Widget featureTestHost(
  Widget child, {
  String locale = 'ar',
  bool dark = false,
  double scale = 1,
}) => EasyLocalization(
  supportedLocales: const [Locale('ar'), Locale('en')],
  startLocale: Locale(locale),
  fallbackLocale: const Locale('en'),
  saveLocale: false,
  path: 'unused',
  assetLoader: const FeatureTestTranslations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    enableScaleWH: () => false,
    enableScaleText: () => false,
    fontSizeResolver: (size, _) => size.toDouble(),
    builder: (context, _) => ToastificationWrapper(
      child: MaterialApp(
        navigatorKey: Go.navigatorKey,
        theme: dark ? SokounTheme.dark : SokounTheme.light,
        locale: context.locale,
        supportedLocales: context.supportedLocales,
        localizationsDelegates: context.localizationDelegates,
        home: Builder(
          builder: (context) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: true,
            ),
            child: child,
          ),
        ),
      ),
    ),
  ),
);

Future<void> mountFeatureTest(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(featureTestHost(child));
  await tester.pumpAndSettle();
}
