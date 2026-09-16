import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';

class OtpCubit extends AsyncCubit<Map<String, dynamic>> {
  OtpCubit() : super(const {});

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
