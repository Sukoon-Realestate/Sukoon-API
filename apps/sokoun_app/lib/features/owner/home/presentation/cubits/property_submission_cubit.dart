import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

import '../../data/models/owner_add_property_content.dart';
import '../../data/property_submission_data.dart';

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
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        PropertySubmissionData.request(form: form, propertyId: propertyId),
      ),
      onSuccess: (model) => onSuccess(model.data),
    );
  }
}
