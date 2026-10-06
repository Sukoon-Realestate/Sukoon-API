import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/helpers/validators.dart';

class ForgotPasswordCubit extends AsyncCubit<Map<String, dynamic>> {
  ForgotPasswordCubit() : super(const {});

  Future<void> sendResetLink({
    required String email,
    required void Function() onSuccess,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.resetPassword,
          httpRequestType: HttpRequestType.post,
          body: <String, dynamic>{'email': Validators.normalizeEmail(email)},
          mapper: (json) =>
              json is Map<String, dynamic> ? json : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
