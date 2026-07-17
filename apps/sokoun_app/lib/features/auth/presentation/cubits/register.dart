import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/auth/data/models/register.dart';

class RegisterCubit extends AsyncCubit<String> {
  RegisterCubit() : super('');

  Future<void> register({
    required RegisterBody body,
    void Function()? onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () async => await baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.register,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
        ),
      ),
      onSuccess: (_) => onSuccess?.call(),
    );
  }
}
