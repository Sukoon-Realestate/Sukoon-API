import 'helpers/account_test_dependencies.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/account_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/forgot_password.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notification_settings_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_settings_tile.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/available_places_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_filter_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Repository repository;
  late _Network network;

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
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (_) async => null,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
  });
  setUp(() async {
    await injector.reset();
    AccountSession.end();
    repository = _Repository();
    network = _Network();
    injector
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      )
      ..registerSingleton<NetworkService>(network);
  });
  tearDown(() async {
    await injector.reset();
    AccountSession.end();
  });

  test(
    'profile opened during account startup joins the account request',
    () async {
      await registerAuthenticatedTestAccount();
      final cubit = AccountCubit();
      addTearDown(cubit.close);
      final startup = cubit.getAccount();
      final profile = cubit.getAccount();
      expect(profile, same(startup));
      expect(repository.requests, hasLength(1));
      repository.requests.single.complete({
        'user': {'id': '1'},
      });
      await Future.wait([startup, profile]);
      expect(cubit.state.isSuccess, isTrue);
      final refresh = cubit.getAccount();
      expect(repository.requests, hasLength(2));
      repository.requests.last.complete({
        'user': {'id': '1'},
      });
      await refresh;
    },
  );

  test(
    'available places shares a pending selection and ignores stale responses',
    () async {
      final cubit = AvailablePlacesCubit();
      addTearDown(cubit.close);
      final first = cubit.getAvailablePlaces('apartment');
      expect(cubit.getAvailablePlaces('apartment'), same(first));
      final second = cubit.getAvailablePlaces('villa');
      expect(repository.requests.first.params.cancelToken?.isCancelled, isTrue);
      expect(repository.requests.last.params.cancelToken?.isCancelled, isFalse);
      expect(repository.requests, hasLength(2));
      repository.requests[1].complete({
        'places': [
          {'city': 'new'},
        ],
      });
      await second;
      repository.requests[0].complete({
        'places': [
          {'city': 'old'},
        ],
      });
      await first;
      expect(cubit.data.places.single.city, 'new');
      final refresh = cubit.retry();
      expect(repository.requests, hasLength(3));
      repository.requests.last.complete({'places': []});
      await refresh;
    },
  );

  test('calendar coalesces the same day and keeps the newest day', () async {
    final firstDate = DateTime(2026, 10, 1);
    final secondDate = DateTime(2026, 10, 2);
    final cubit = OwnerCalendarCubit(initialDate: firstDate);
    addTearDown(cubit.close);
    final first = cubit.getCalendar(date: firstDate);
    expect(cubit.getCalendar(date: firstDate), same(first));
    final second = cubit.getCalendar(date: secondDate);
    expect(repository.requests.first.params.cancelToken?.isCancelled, isTrue);
    expect(repository.requests.last.params.cancelToken?.isCancelled, isFalse);
    expect(repository.requests, hasLength(2));
    repository.requests[1].complete({});
    await second;
    repository.requests[0].complete({});
    await first;
    expect(cubit.data.selectedDateValue, secondDate);
  });

  test('closed and changed-session Cubits ignore late results', () async {
    final cubit = AvailablePlacesCubit();
    final pending = cubit.getAvailablePlaces('apartment');
    final state = cubit.state;
    AccountSession.begin('another-user');
    repository.requests.single.complete({
      'places': [
        {'city': 'old-session'},
      ],
    });
    await pending;
    expect(cubit.state, state);
    await cubit.close();
    expect(repository.requests.single.params.cancelToken?.isCancelled, isTrue);
    await cubit.getAvailablePlaces('villa');
    expect(repository.requests, hasLength(1));
  });

  test(
    'repeat submissions send once; a subsequent explicit submission is allowed',
    () async {
      final cubit = ForgotPasswordCubit();
      addTearDown(cubit.close);
      int successes = 0;
      Future<void> submit() => cubit.sendResetLink(
        email: 'tenant@example.com',
        onSuccess: () => successes++,
      );
      final first = submit();
      await submit();
      expect(repository.requests, hasLength(1));
      repository.requests.single.complete({});
      await first;
      expect(successes, 1);
      final retry = submit();
      expect(repository.requests, hasLength(2));
      repository.requests.last.complete({});
      await retry;
      expect(successes, 2);
    },
  );

  test('saves for distinct property IDs remain independent', () async {
    final cubit = PropertySaveCubit();
    addTearDown(cubit.close);
    final first = cubit.saveProperty(propertyId: 'one', onError: (_) {});
    final second = cubit.saveProperty(propertyId: 'two', onError: (_) {});
    expect(repository.requests, hasLength(2));
    for (final request in repository.requests) {
      request.complete({});
    }
    await Future.wait([first, second]);
  });

  test(
    'device registration coalesces calls before authentication finishes',
    () async {
      final source = NotificationDeviceApiDataSource();
      network.sessionGate = Completer<bool>();
      final first = source.registerToken('token');
      final duplicate = source.registerToken('token');
      expect(network.sessionChecks, 1);
      network.sessionGate!.complete(true);
      await Future.wait([first, duplicate]);
      await source.registerToken('token');
      expect(network.requests, hasLength(1));
      AccountSession.begin('another-user');
      await source.registerToken('token');
      expect(network.requests, hasLength(2));
    },
  );

  test(
    'token rotation during registration sends the new token afterward',
    () async {
      final source = NotificationDeviceApiDataSource();
      network.requestGate = Completer<void>();
      final first = source.registerToken('old');
      await Future<void>.delayed(Duration.zero);
      final rotated = source.registerToken('new');
      expect(network.requests, hasLength(1));
      network.requestGate!.complete();
      await Future.wait([first, rotated]);
      expect(network.requests.map((request) => request.body?['token']), [
        'old',
        'new',
      ]);
    },
  );

  test('local device cleanup sends no unregister endpoint', () async {
    final source = NotificationDeviceApiDataSource();
    await source.registerToken('token');
    await source.unregisterCurrentDevice(notifyServer: false);
    expect(network.requests.map((request) => request.path), [
      ApiConstants.notificationDevices,
    ]);
  });

  test(
    'local device cleanup cancels registration waiting for cookies',
    () async {
      final source = NotificationDeviceApiDataSource();
      network.sessionGate = Completer<bool>();
      final registration = source.registerToken('token');
      final stopped = source.unregisterCurrentDevice(notifyServer: false);
      network.sessionGate!.complete(true);
      await Future.wait([registration, stopped]);
      expect(network.requests, isEmpty);
    },
  );

  test('local device cleanup cancels delayed device startup', () async {
    final source = NotificationDeviceApiDataSource();
    network.sessionGate = Completer<bool>();
    final starting = source.start();
    await source.unregisterCurrentDevice(notifyServer: false);
    network.sessionGate!.complete(true);
    await starting;
    expect(network.requests, isEmpty);
  });

  test(
    'late registration cannot block or clear the next login registration',
    () async {
      final source = NotificationDeviceApiDataSource();
      final oldResponse = Completer<void>();
      network.requestGate = oldResponse;
      final previous = source.registerToken('old-token');
      await pumpEventQueue();
      expect(network.requests, hasLength(1));

      await source.unregisterCurrentDevice(notifyServer: false);
      AccountSession.begin('next-account');
      final newResponse = Completer<void>();
      network.requestGate = newResponse;
      final current = source.registerToken('new-token');
      await pumpEventQueue();
      expect(network.requests, hasLength(2));
      oldResponse.complete();
      await previous;
      final duplicate = source.registerToken('new-token');
      expect(duplicate, same(current));
      newResponse.complete();
      await Future.wait([current, duplicate]);

      expect(network.requests.map((request) => request.body?['token']), [
        'old-token',
        'new-token',
      ]);
    },
  );

  test('device registration failure remains retryable', () async {
    final source = NotificationDeviceApiDataSource();
    network.failRequest = true;
    await source.registerToken('token');
    network.failRequest = false;
    await source.registerToken('token');
    expect(network.requests, hasLength(2));
  });

  testWidgets('search cancels replaced pages and requests on disposal', (
    tester,
  ) async {
    network.requestGate = Completer<void>();
    await _pump(
      tester,
      const TenantSearchResultsScreen(
        initialFilters: PropertySearchFilters.initial(),
        initialFilterOptions: PropertyFilterOptionsModel.initial(),
      ),
      settle: false,
    );
    expect(network.requests, hasLength(1));
    final first = network.requests.single.cancelToken!;
    await tester.enterText(find.byType(TextField).first, 'villa');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pump();
    await tester.pump();
    expect(first.isCancelled, isTrue);
    expect(network.requests, hasLength(2));
    final second = network.requests.last.cancelToken!;
    expect(second.isCancelled, isFalse);
    await tester.pumpWidget(const SizedBox.shrink());
    expect(second.isCancelled, isTrue);
    network.requestGate!.complete();
    await tester.pump();
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'search listings load independently and filters reuse loaded options',
    (tester) async {
      await _pump(
        tester,
        const TenantSearchResultsScreen(
          initialFilters: PropertySearchFilters.initial(),
        ),
      );
      expect(repository.requests, hasLength(1));
      expect(network.requests, hasLength(1));
      expect(find.byType(AppPagify<PropertyDetailsModel>), findsOneWidget);
      final scaffold = tester.widget<AppScaffold>(find.byType(AppScaffold));
      repository.requests.single.complete({});
      await tester.pumpAndSettle();
      expect(
        network.requests.where(
          (request) => request.path == ApiConstants.properties,
        ),
        hasLength(1),
      );
      expect(
        tester.widget<AppScaffold>(find.byType(AppScaffold)),
        same(scaffold),
      );
      expect(tester.takeException(), isNull, reason: 'before opening filters');
      await tester.tap(find.byIcon(Icons.tune_rounded));
      await tester.pumpAndSettle();
      expect(find.byType(TenantFilterScreen), findsOneWidget);
      expect(repository.requests, hasLength(1));
      expect(tester.takeException(), isNull, reason: 'after opening filters');
      Go.back();
      await tester.pumpAndSettle();
      expect(
        tester.takeException(),
        isNull,
        reason: 'after returning from filters',
      );
      tester.view.physicalSize = const Size(768, 1024);
      await tester.pumpAndSettle();
      expect(network.requests, hasLength(1));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'updating one notification setting preserves other tiles and scaffold',
    (tester) async {
      await _pump(
        tester,
        const NotificationSettingsScreen(role: NotificationRole.tenant),
      );
      repository.requests.single.complete({});
      await tester.pumpAndSettle();
      final tiles = tester
          .widgetList<NotificationSettingsTile>(
            find.byType(NotificationSettingsTile),
          )
          .toList();
      final scaffold = tester.widget<AppScaffold>(find.byType(AppScaffold));
      tiles.first.onChanged(true);
      await tester.pump();
      await tester.pump();
      expect(repository.requests, hasLength(2));
      final updated = tester
          .widgetList<NotificationSettingsTile>(
            find.byType(NotificationSettingsTile),
          )
          .toList();
      expect(updated.first.isUpdating, isTrue);
      expect(updated.first.setting.isEnabled, isTrue);
      for (int index = 1; index < tiles.length; index++) {
        expect(updated[index], same(tiles[index]));
      }
      expect(
        tester.widget<AppScaffold>(find.byType(AppScaffold)),
        same(scaffold),
      );
      repository.requests.last.complete({});
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pump(
  WidgetTester tester,
  Widget screen, {
  bool settle = true,
}) async {
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
          navigatorKey: Go.navigatorKey,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
          home: MediaQuery(
            data: MediaQuery.of(context).copyWith(disableAnimations: true),
            child: screen,
          ),
        ),
      ),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
  }
}

class _Repository implements BaseRepository {
  final List<_Request> requests = [];
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    final request = _Request(params);
    requests.add(request);
    final json = await request.response.future;
    return Success(
      BaseModel<T>(
        key: '',
        msg: '',
        data: params.mapper == null ? json as T : params.mapper!(json),
      ),
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Request {
  _Request(this.params);
  final CrudBaseParmas params;
  final Completer<Map<String, dynamic>> response = Completer();
  void complete(Map<String, dynamic> json) => response.complete(json);
}

class _Network implements NetworkService {
  final List<NetworkRequest> requests = [];
  Completer<bool>? sessionGate;
  Completer<void>? requestGate;
  int sessionChecks = 0;
  bool failRequest = false;
  @override
  Future<bool> hasSessionCookies() async {
    sessionChecks++;
    return sessionGate == null ? true : await sessionGate!.future;
  }

  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) async {
    requests.add(request);
    await requestGate?.future;
    if (failRequest) throw StateError('offline');
    const json = <String, dynamic>{
      'count': 0,
      'results': [],
      'per_page': 20,
      'total_pages': 1,
    };
    return BaseModel<T>(
      key: '',
      msg: '',
      data: mapper == null ? json as T : mapper(json),
    );
  }

  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<void> updateBaseUrl() async {}
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/en.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
