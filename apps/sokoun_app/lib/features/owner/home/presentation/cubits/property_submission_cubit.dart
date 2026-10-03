import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

import '../../data/models/owner_add_property_content.dart';

class PropertySubmissionCubit extends AsyncCubit<PropertyDetailsModel> {
  PropertySubmissionCubit() : super(const PropertyDetailsModel.initial());

  Future<void> save({
    required OwnerAddPropertyFormState form,
    String? propertyId,
    required void Function(PropertyDetailsModel property) onSuccess,
  }) async {
    if (isClosed || isLoading || !form.isBasicsReady || !form.isPricingReady) {
      return;
    }
    final bool isCreating = propertyId == null;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: isCreating
              ? ApiConstants.createProperty
              : ApiConstants.propertyDetails(propertyId),
          httpRequestType: isCreating
              ? HttpRequestType.post
              : HttpRequestType.patch,
          body: form.toJson(includeMainImage: isCreating),
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
