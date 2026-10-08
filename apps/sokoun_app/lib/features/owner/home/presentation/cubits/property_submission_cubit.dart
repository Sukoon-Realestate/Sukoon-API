import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_inventory_confirmation.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

import '../../data/models/owner_add_property_content.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';

class PropertySubmissionCubit
    extends VerifiedActionCubit<PropertyDetailsModel> {
  PropertySubmissionCubit({
    this.capabilities = RentalOfferCapabilities.configured,
  }) : super(const PropertyDetailsModel.initial());
  final RentalOfferCapabilities capabilities;
  PropertyDetailsModel? recoveryProperty;

  Future<void> save({
    required OwnerAddPropertyFormState form,
    String? propertyId,
    required void Function(PropertyDetailsModel property) onSuccess,
  }) async {
    if (isClosed || isLoading || !checkVerification()) return;
    if (!form.canSaveToServer(capabilities)) {
      setError();
      updateErrorMessage(
        form.submissionInventory?.hasLocalOnlyDetails == true
            ? LocaleKeys.rentalDraftDetailsHelp
            : LocaleKeys.rentalUnavailableCapability,
      );
      return;
    }
    if (isClosed ||
        isLoading ||
        (propertyId == null && form.videoFile == null) ||
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
          body: form.toJson(isEditing: !isCreating, capabilities: capabilities),
          headers: form.needsOfferCapability
              ? {
                  if (isCreating) 'Idempotency-Key': form.submissionKey,
                  'X-Rental-Offers-Version': '1',
                }
              : null,
          isFromData: true,
          sendTimeout: ConstantManager.uploadSendTimeout,
          mapper: (json) {
            final PropertyDetailsModel property = PropertyDetailsModel.fromJson(
              Map<String, dynamic>.from(json as Map),
            );
            if (property.id.trim().isEmpty) {
              throw const FormatException('Missing saved property ID');
            }
            recoveryProperty = property;
            if (form.needsOfferCapability &&
                !RentalInventoryConfirmation.matches(
                  form.submissionInventory!,
                  property.rentalInventory,
                  includeMedia: capabilities.canAssociateMedia,
                )) {
              throw FormatException(LocaleKeys.rentalIncompatibleResponse);
            }
            return property;
          },
        ),
      ),
      onSuccess: (model) {
        ObjectBoxCacheService.remove('property_details_${model.data.id}');
        ObjectBoxCacheService.remove('owner_properties');
        for (final status in ['under_review', 'accepted', 'rejected']) {
          ObjectBoxCacheService.remove('owner_properties_$status');
        }
        ObjectBoxCacheService.remove('owner_dashboard');
        onSuccess(model.data);
      },
    );
  }
}
