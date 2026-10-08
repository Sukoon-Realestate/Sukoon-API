import 'dart:async';

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
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/account_cubit.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel secureStorage = MethodChannel(
    'plugins.it_nomads.com/flutter_secure_storage',
  );
  late _AccountRepository repository;
  late _SessionNetwork network;
  late UserCubit userCubit;
  late AccountCubit accountCubit;

  setUpAll(() async {
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(
      preferences,
      (call) async => call.method == 'getAll' ? <String, Object>{} : true,
    );
    messenger.setMockMethodCallHandler(secureStorage, (_) async => null);
    await CacheStorage.init();
  });

  setUp(() async {
    await injector.reset();
    await CacheStorage.deleteAll();
    AccountSession.end();
    repository = _AccountRepository();
    network = _SessionNetwork();
    userCubit = UserCubit();
    injector
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      )
      ..registerSingleton<NetworkService>(network)
      ..registerSingleton<UserCubit>(userCubit);
    accountCubit = AccountCubit();
  });

  tearDown(() async {
    await accountCubit.close();
    await userCubit.close();
    await injector.reset();
    AccountSession.end();
  });

  tearDownAll(() {
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(preferences, null);
    messenger.setMockMethodCallHandler(secureStorage, null);
  });

  test(
    'maps nested account identity and contact details and round-trips the cache',
    () {
      final UserModel user = UserModel.fromJson(_accountResponse);
      expect(user.id, '17');
      expect(user.name, 'Updated account');
      expect(user.phone, '0500000000');
      expect(user.email, 'updated@example.com');
      expect(user.isVerified, isTrue);
      expect(user.copyWith(name: 'Edited').isVerified, isTrue);
      expect(UserModel.fromJson(user.toJson()).toJson(), user.toJson());
      expect(user.copyWith(name: 'Edited').id, '17');
    },
  );

  test(
    'loads cookie-authenticated account and persists it before completion',
    () async {
      await accountCubit.getAccount();
      final AccountContent profile = accountCubit.data;
      expect(repository.requests, 1);
      expect(repository.lastApi, ApiConstants.getAccData);
      expect(repository.lastMethod, HttpRequestType.get);
      expect(repository.lastCacheKey, isNull);
      expect(accountCubit.state.isSuccess, isTrue);
      expect(userCubit.isUserLoggedIn, isTrue);
      expect(userCubit.user.toJson(), UserModel.currentUser?.toJson());
      expect(UserModel.currentUser?.email, 'updated@example.com');
      expect(UserModel.currentUser?.isVerified, isTrue);
      expect(profile.stats.savedCount, 3);

      final UserCubit restored = UserCubit();
      addTearDown(restored.close);
      expect(await restored.init(), isTrue);
      expect(restored.user.toJson(), userCubit.user.toJson());
      expect(restored.user.isVerified, isTrue);
    },
  );

  test(
    'refreshing the same user preserves the active session generation',
    () async {
      await userCubit.setUserLoggedIn(
        user: const UserModel(id: '17', name: 'Old', phone: '', email: ''),
      );
      final int generation = AccountSession.generation;
      await accountCubit.getAccount();
      expect(AccountSession.generation, generation);
      expect(UserModel.currentUser?.name, 'Updated account');
    },
  );

  test('guest without cookies does not request or cache an account', () async {
    network.hasCookies = false;
    await accountCubit.getAccount();
    expect(repository.requests, 0);
    expect(UserModel.currentUser, isNull);
    expect(userCubit.isUserLoggedIn, isFalse);
  });

  test(
    'my-account false overrides earlier verification and menu badges',
    () async {
      await userCubit.setUserLoggedIn(
        user: const UserModel(
          id: '17',
          name: '',
          phone: '',
          email: '',
          isVerified: true,
        ),
      );
      repository.response = {
        ..._accountResponse,
        'is_verified': false,
        'menu_items': {
          'verification': {'is_verified': true},
        },
      };
      await accountCubit.getAccount();
      expect(accountCubit.data.user.isVerified, isFalse);
      expect(userCubit.user.isVerified, isFalse);
      expect(UserModel.currentUser?.isVerified, isFalse);
      await userCubit.updateUser(userCubit.user.copyWith(name: 'Edited'));
      expect(userCubit.user.isVerified, isFalse);
    },
    skip: UserModel.bypassVerification,
  );

  test('profile edits update the shared account without refetching', () async {
    await accountCubit.getAccount();
    final int savedCount = accountCubit.data.stats.savedCount;
    await userCubit.updateUser(
      userCubit.user.copyWith(name: 'Edited account', phone: '0511111111'),
    );
    await Future<void>.delayed(Duration.zero);

    expect(repository.requests, 1);
    expect(accountCubit.data.user.fullName, 'Edited account');
    expect(accountCubit.data.accountDetails.phoneNumber, '0511111111');
    expect(accountCubit.data.stats.savedCount, savedCount);
  });

  for (final bool closeCubit in [false, true]) {
    test(
      'ignores a response after ${closeCubit ? 'leaving the screen' : 'the session ends'}',
      () async {
        repository.gate = Completer<void>();
        final Future<void> request = accountCubit.getAccount();
        await repository.started.future;
        if (closeCubit) {
          await accountCubit.close();
        } else {
          AccountSession.end();
        }
        repository.gate!.complete();
        await request;
        expect(UserModel.currentUser, isNull);
        expect(userCubit.isUserLoggedIn, isFalse);
      },
    );
  }

  for (final bool invalidResponse in [false, true]) {
    testWidgets(
      '${invalidResponse ? 'invalid account' : 'failed request'} keeps the cached user',
      (tester) async {
        await userCubit.setUserLoggedIn(
          user: const UserModel(
            id: '17',
            name: 'Cached account',
            phone: '',
            email: 'cached@example.com',
          ),
        );
        final Map<String, dynamic> cached = UserModel.currentUser!.toJson();
        if (invalidResponse) {
          repository.response = const {
            'user': {'full_name': 'Missing identity'},
          };
        } else {
          repository.failure = const Failure('Unable to refresh account');
        }
        await tester.pumpWidget(
          ScreenUtilInit(
            designSize: const Size(360, 690),
            builder: (_, _) => MaterialApp(
              navigatorKey: Go.navigatorKey,
              home: const Scaffold(),
            ),
          ),
        );
        await accountCubit.getAccount();
        expect(accountCubit.state.isError, isTrue);
        expect(UserModel.currentUser?.toJson(), cached);
        expect(userCubit.isUserLoggedIn, isTrue);
        await tester.pumpAndSettle();
        await tester.pump(const Duration(seconds: 5));
        await tester.pumpAndSettle();
      },
    );
  }
}

const Map<String, dynamic> _accountResponse = {
  'user': {'id': 17, 'full_name': 'Updated account', 'is_verified': true},
  'account_details': {
    'email': 'updated@example.com',
    'phone_number': '0500000000',
  },
  'stats': {'saved_count': 3, 'visits_count': 2, 'reviews_count': 1},
};

class _AccountRepository implements BaseRepository {
  int requests = 0;
  String? lastApi;
  HttpRequestType? lastMethod;
  String? lastCacheKey;
  Map<String, dynamic> response = _accountResponse;
  Failure? failure;
  Completer<void>? gate;
  final Completer<void> started = Completer<void>();

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests++;
    lastApi = params.api;
    lastMethod = params.httpRequestType;
    lastCacheKey = params.cacheKey;
    if (!started.isCompleted) started.complete();
    await gate?.future;
    if (failure != null) return Error(failure!);
    try {
      return Success(
        BaseModel<T>(key: '', msg: '', data: params.mapper!(response)),
      );
    } on FormatException catch (error) {
      return Error(Failure(error.message));
    }
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _SessionNetwork implements NetworkService {
  bool hasCookies = true;

  @override
  Future<bool> hasSessionCookies() async => hasCookies;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
