import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

import '../../data/models/owner_add_property_content.dart';

class PropertySubmissionCubit extends AsyncCubit<PropertyDetailsModel> {
  PropertySubmissionCubit() : super(const PropertyDetailsModel.initial());

  Future<void> save({
    required OwnerAddPropertyFormState form,
    String? propertyId,
    required void Function(PropertyDetailsModel property) onSuccess,
  }) async {
    if (isClosed ||
        isLoading ||
        !form.isBasicsReady ||
        !form.isPhotosReady ||
        !form.isPricingReady) {
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
          body: form.toJson(isEditing: !isCreating),
          isFromData: true,
          sendTimeout: ConstantManager.uploadSendTimeout,
          mapper: (json) {
            final PropertyDetailsModel property = PropertyDetailsModel.fromJson(
              Map<String, dynamic>.from(json as Map),
            );
            if (property.id.trim().isEmpty) {
              throw const FormatException('Missing saved property ID');
            }
            return property;
          },
        ),
      ),
      onSuccess: (model) {
        ObjectBoxCacheService.remove('property_details_${model.data.id}');
        ObjectBoxCacheService.remove('owner_properties');
        ObjectBoxCacheService.remove('owner_dashboard');
        onSuccess(model.data);
      },
    );
  }
}
