import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/otp_screen.dart';

class LoginCubit extends AsyncCubit<Map<String, dynamic>> {
  LoginCubit() : super({});

  Future<void> login({
    required String email,
    required String password,
    required Future<void> Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () async => await baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.login,
          httpRequestType: HttpRequestType.post,
          body: {"email": email, "password": password},
        ),
      ),

      onSuccess: (_) => onSuccess.call(),
    );
  }
}
