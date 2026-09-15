import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/google_login.dart';

void main() {
  late _GoogleLoginRepository repository;
  late _RecordingUserCubit userCubit;

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

  test('posts the Google token and caches the returned user', () async {
    final GoogleLoginCubit cubit = GoogleLoginCubit();
    addTearDown(cubit.close);
    bool completed = false;

    await cubit.login(
      body: const GoogleLoginBody(token: 'google-id-token'),
      onSuccess: () => completed = true,
    );

    expect(ApiConstants.googleLogin, 'auth/google/');
    expect(repository.lastApi, ApiConstants.googleLogin);
    expect(repository.lastMethod, HttpRequestType.post);
    expect(repository.lastBody, {'token': 'google-id-token'});
    expect(userCubit.cachedUser?.id, 17);
    expect(userCubit.cachedUser?.email, 'user@example.com');
    expect(userCubit.cachedUser?.type, 'tenant');
    expect(completed, isTrue);
  });
}

class _GoogleLoginRepository implements BaseRepository {
  String lastApi = '';
  HttpRequestType? lastMethod;
  Map<String, dynamic>? lastBody;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    lastApi = params.api;
    lastMethod = params.httpRequestType;
    lastBody = params.body;
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
