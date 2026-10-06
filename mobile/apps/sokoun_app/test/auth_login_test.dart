import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/login.dart';
import 'package:sokoun_app/features/shared/auth/data/auth_session_data.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late _LoginRepository repository;
  late _RecordingUserCubit userCubit;
  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await CacheStorage.init();
    await CacheStorage.write('current_user_type', 'tenant');
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  setUp(() async {
    await injector.reset();
    repository = _LoginRepository();
    userCubit = _RecordingUserCubit();
    injector
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      )
      ..registerSingleton<UserCubit>(userCubit);
  });

  tearDown(() => injector.reset());

  test(
    'logs in and leaves the shared account cache to the main view',
    () async {
      final LoginCubit cubit = LoginCubit();
      addTearDown(cubit.close);
      bool completed = false;

      await cubit.login(
        email: 'user@example.com',
        password: 'password',
        onSuccess: () => completed = true,
      );

      expect(ApiConstants.currentUser, 'auth/users/me/');
      expect(repository.apis, [ApiConstants.login, ApiConstants.currentUser]);
      expect(repository.methods, [HttpRequestType.post, HttpRequestType.get]);
      expect(repository.bodies, [
        {'email': 'user@example.com', 'password': 'password'},
        null,
      ]);
      expect(userCubit.cachedUser, isNull);
      expect(cubit.data.id, '17');
      expect(cubit.data.email, 'user@example.com');
      expect(cubit.data.type, 'tenant');
      expect(repository.currentUserCacheKey, isNull);
      expect(repository.cachedUserJson, isNull);
      expect(repository.restoredUser, isNull);
      expect(cubit.data.name, 'Test User');
      expect(completed, isTrue);
    },
  );

  test(
    'failed fresh identity lookup clears the provisional cookie session',
    () async {
      repository.currentUserFailure = const Failure('Cannot load account');
      final _SessionNetwork network = _SessionNetwork();
      injector.registerSingleton<NetworkService>(network);

      final result = await const AuthSessionApiDataSource()
          .loginWithCredentials(
            email: 'user@example.com',
            password: 'password',
          );

      expect(result.tryGetError(), repository.currentUserFailure);
      expect(network.cookiesCleared, isTrue);
      expect(userCubit.cachedUser, isNull);
      expect(repository.currentUserCacheKey, isNull);
    },
  );
}

class _LoginRepository implements BaseRepository {
  final List<String> apis = [];
  final List<HttpRequestType> methods = [];
  final List<Map<String, dynamic>?> bodies = [];
  String? currentUserCacheKey;
  Map<String, dynamic>? cachedUserJson;
  UserModel? restoredUser;
  Failure? currentUserFailure;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    apis.add(params.api);
    methods.add(params.httpRequestType);
    bodies.add(params.body);
    if (params.api == ApiConstants.login) {
      return Success(
        BaseModel<T>(key: '', msg: '', data: const <String, dynamic>{} as T),
      );
    }

    if (currentUserFailure != null) return Error(currentUserFailure!);

    final T user = params.mapper!(const <String, dynamic>{
      'id': 17,
      'name': 'Test User',
      'full_name': 'Test User',
      'phone': '01000000000',
      'email': 'user@example.com',
      'type': 'tenant',
    });
    currentUserCacheKey = params.cacheKey;
    cachedUserJson = params.toJson?.call(user);
    restoredUser = cachedUserJson == null
        ? null
        : params.fromCacheJson?.call(cachedUserJson!) as UserModel?;
    return Success(BaseModel<T>(key: '', msg: '', data: user));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _SessionNetwork implements NetworkService {
  bool cookiesCleared = false;

  @override
  Future<void> clearSessionCookies() async => cookiesCleared = true;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _RecordingUserCubit extends UserCubit {
  UserModel? cachedUser;

  @override
  Future<void> setUserLoggedIn({required UserModel user}) async {
    cachedUser = user;
  }
}
