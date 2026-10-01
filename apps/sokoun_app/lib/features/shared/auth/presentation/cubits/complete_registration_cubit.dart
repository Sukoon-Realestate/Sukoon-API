import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import '../../data/models/complete_registration_result.dart';
import '../../data/models/kyc_upload_documents_data.dart';

class CompleteRegistrationCubit extends AsyncCubit<CompleteRegistrationResult> {
  CompleteRegistrationCubit()
    : super(const CompleteRegistrationResult.initial());

  Future<void> submit(
    KycUploadDocumentsData body, {
    required void Function(CompleteRegistrationResult result) onResult,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<CompleteRegistrationResult>(
          api: ApiConstants.completeRegister,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          isFromData: true,
          sendTimeout: ConstantManager.uploadSendTimeout,
          mapper: (json) => CompleteRegistrationResult.fromJson(
            Map<String, dynamic>.from(json as Map),
          ),
        ),
      ),
      onSuccess: (response) => onResult(response.data),
    );
  }
}
