import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/google_login.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late _GoogleLoginRepository repository;
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
    repository = _GoogleLoginRepository();
    userCubit = _RecordingUserCubit();
    injector
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      )
      ..registerSingleton<UserCubit>(userCubit);
  });

  tearDown(() => injector.reset());

  test(
    'posts the Google token, fetches the current user, and caches it',
    () async {
      final GoogleLoginCubit cubit = GoogleLoginCubit();
      addTearDown(cubit.close);
      bool completed = false;

      await cubit.login(
        body: const GoogleLoginBody(token: 'google-id-token'),
        onSuccess: () => completed = true,
      );

      expect(ApiConstants.googleLogin, 'auth/google/');
      expect(ApiConstants.currentUser, 'auth/users/me/');
      expect(repository.apis, [
        ApiConstants.googleLogin,
        ApiConstants.currentUser,
      ]);
      expect(repository.methods, [HttpRequestType.post, HttpRequestType.get]);
      expect(repository.bodies, [
        {'token': 'google-id-token'},
        null,
      ]);
      expect(userCubit.cachedUser?.id, '17');
      expect(userCubit.cachedUser?.email, 'user@example.com');
      expect(userCubit.cachedUser?.type, 'tenant');
      expect(repository.currentUserCacheKey, isNull);
      expect(repository.cachedUserJson, isNull);
      expect(repository.restoredUser, isNull);
      expect(userCubit.cachedUser?.name, 'Test User');
      expect(completed, isTrue);
    },
  );
}

class _GoogleLoginRepository implements BaseRepository {
  final List<String> apis = [];
  final List<HttpRequestType> methods = [];
  final List<Map<String, dynamic>?> bodies = [];
  String? currentUserCacheKey;
  Map<String, dynamic>? cachedUserJson;
  UserModel? restoredUser;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    apis.add(params.api);
    methods.add(params.httpRequestType);
    bodies.add(params.body);
    if (params.api == ApiConstants.googleLogin) {
      return Success(
        BaseModel<T>(key: '', msg: '', data: const <String, dynamic>{} as T),
      );
    }

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

class _RecordingUserCubit extends UserCubit {
  UserModel? cachedUser;

  @override
  Future<void> setUserLoggedIn({required UserModel user}) async {
    cachedUser = user;
  }
}
