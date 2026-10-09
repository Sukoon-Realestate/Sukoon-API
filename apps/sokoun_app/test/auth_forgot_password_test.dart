import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/forgot_password.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _ForgotPasswordRepository repository;

  setUp(() async {
    await injector.reset();
    repository = _ForgotPasswordRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });

  tearDown(() => injector.reset());

  test('posts the email to the reset password endpoint', () async {
    final ForgotPasswordCubit cubit = ForgotPasswordCubit();
    addTearDown(cubit.close);
    bool completed = false;

    await cubit.sendResetLink(
      email: '  meshzeyad2@gmail.com  ',
      onSuccess: () => completed = true,
    );

    expect(ApiConstants.resetPassword, 'auth/users/reset_password/');
    expect(repository.api, ApiConstants.resetPassword);
    expect(repository.method, HttpRequestType.post);
    expect(repository.body, {'email': 'meshzeyad2@gmail.com'});
    expect(completed, isTrue);
  });
}

class _ForgotPasswordRepository implements BaseRepository {
  String? api;
  HttpRequestType? method;
  Map<String, dynamic>? body;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    api = params.api;
    method = params.httpRequestType;
    body = params.body;
    final T data = params.mapper?.call(null) ?? const <String, dynamic>{} as T;
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
