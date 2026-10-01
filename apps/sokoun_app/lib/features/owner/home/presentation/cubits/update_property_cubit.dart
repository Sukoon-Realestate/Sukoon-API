import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class UpdatePropertyCubit extends AsyncCubit<PropertyDetailsModel> {
  UpdatePropertyCubit() : super(const PropertyDetailsModel.initial());

  Future<void> updateProperty({
    required String propertyId,
    required OwnerAddPropertyFormState form,
    required void Function(PropertyDetailsModel property) onSuccess,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(propertyId),
          httpRequestType: HttpRequestType.patch,
          body: form.toRequestBody(),
          isFromData: true,
          sendTimeout: ConstantManager.uploadSendTimeout,
          mapper: (json) => json is Map<String, dynamic>
              ? PropertyDetailsModel.fromJson(json)
              : const PropertyDetailsModel.initial(),
        ),
      ),
      onSuccess: (model) => onSuccess(model.data),
    );
  }
}
