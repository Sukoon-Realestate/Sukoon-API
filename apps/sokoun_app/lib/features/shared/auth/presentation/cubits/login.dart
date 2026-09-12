import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';

class LoginCubit extends AsyncCubit<Map<String, dynamic>> {
  LoginCubit() : super(const {});

  Future<void> login({
    required String email,
    required String password,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.login,
          httpRequestType: HttpRequestType.post,
          body: {'email': email, 'password': password},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }

  Future<void> verifyOtp({
    required VerifyOtpBody body,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.verifyOtp,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }

  Future<void> resendOtp({
    required ResendOtpBody body,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.resendOtp,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
