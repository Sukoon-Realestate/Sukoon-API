import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class CreatePropertyCubit extends AsyncCubit<PropertyDetailsModel> {
  CreatePropertyCubit() : super(const PropertyDetailsModel.initial());

  Future<void> createProperty({
    required OwnerAddPropertyFormState form,
    required void Function(PropertyDetailsModel property) onSuccess,
  }) async {
    if (isClosed || isLoading || !form.isBasicsReady || !form.isPricingReady) {
      return;
    }
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.createProperty,
          httpRequestType: HttpRequestType.post,
          body: form.toJson(),
          isFromData: true,
          sendTimeout: ConstantManager.uploadSendTimeout,
          mapper: (json) {
            final PropertyDetailsModel property = PropertyDetailsModel.fromJson(
              json as Map<String, dynamic>,
            );
            if (property.id.trim().isEmpty) {
              throw const FormatException('Missing created property ID');
            }
            return property;
          },
        ),
      ),
      onSuccess: (model) => onSuccess(model.data),
    );
  }
}
