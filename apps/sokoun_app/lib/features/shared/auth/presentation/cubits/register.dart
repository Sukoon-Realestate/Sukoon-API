import 'dart:io';

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';

class RegisterCubit extends AsyncCubit<String> {
  RegisterCubit() : super('');

  RegisterBody _registerBody = RegisterBody.initial();

  RegisterBody get registerBody => _registerBody;

  void updateRegisterBody(RegisterBody body) {
    _registerBody = body;
  }

  void updateKycDocuments({
    required String nationalId,
    File? frontIdImage,
    File? backIdImage,
    File? selfieImage,
  }) {
    _registerBody = _registerBody.copyWith(
      nationalId: nationalId,
      frontIdImage: frontIdImage,
      backIdImage: backIdImage,
      selfieImage: selfieImage,
    );
  }

  Future<void> register({void Function()? onSuccess}) async {
    final RegisterBody requestBody = _registerBody;

    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas(
          api: ApiConstants.register,
          httpRequestType: HttpRequestType.post,
          body: requestBody.toJson(),
          isFromData: requestBody.hasFiles,
        ),
      ),
      onSuccess: (_) => onSuccess?.call(),
    );
  }
}
