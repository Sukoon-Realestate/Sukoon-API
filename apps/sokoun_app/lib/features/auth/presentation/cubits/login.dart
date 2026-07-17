import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

class LoginCubit extends AsyncCubit<String> {
  LoginCubit() : super('');

  Future<void> login({
    required String email,
    required String password
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () async => await baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.login,
          httpRequestType: HttpRequestType.post,
          body: {
            "email": email,
            "password": password
          },
        ),
      ),
    );
  }
}
