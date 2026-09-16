import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/login.dart';

void main() {
  late _LoginRepository repository;
  late _RecordingUserCubit userCubit;

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
    'logs in, fetches the current user, caches it, then completes',
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
      expect(userCubit.cachedUser?.id, '17');
      expect(userCubit.cachedUser?.email, 'user@example.com');
      expect(userCubit.cachedUser?.type, 'tenant');
      expect(completed, isTrue);
    },
  );
}

class _LoginRepository implements BaseRepository {
  final List<String> apis = [];
  final List<HttpRequestType> methods = [];
  final List<Map<String, dynamic>?> bodies = [];

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

    final T user = params.mapper!(const <String, dynamic>{
      'id': 17,
      'name': 'Test User',
      'phone': '01000000000',
      'email': 'user@example.com',
      'type': 'tenant',
    });
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
