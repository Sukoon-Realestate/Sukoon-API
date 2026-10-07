import 'dart:convert';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/rental_selection.dart';
import '../../data/rental_inventory_validation.dart';
import '../../data/rental_inventory_confirmation.dart';
import '../../data/rental_offer_capabilities.dart';

/// Proposed v1 extension of the existing property PATCH, never a visit update.
class RentalInventoryMutationCubit extends AsyncCubit<PropertyDetailsModel> {
  RentalInventoryMutationCubit({
    this.capabilities = RentalOfferCapabilities.configured,
  }) : super(const PropertyDetailsModel.initial());
  final RentalOfferCapabilities capabilities;

  Future<void> updateOffer({
    required RentalSelection selection,
    String? availability,
    bool archive = false,
    required void Function(PropertyDetailsModel) onSuccess,
  }) async {
    if (isLoading || isClosed) return;
    if (!capabilities.canWrite ||
        !capabilities.canManageInventory ||
        !selection.canIdentify) {
      setError(errorMessage: LocaleKeys.rentalUnavailableCapability);
      return;
    }
    // Fresh ownership/actions/revision, with a complete cache contract for reads.
    final generation = AccountSession.generation;
    setLoading();
    final result = await baseCrudUseCase.call(
      CrudBaseParmas<PropertyDetailsModel>(
        api: ApiConstants.propertyDetails(selection.propertyId),
        httpRequestType: HttpRequestType.get,
        cacheKey: 'property_details_${selection.propertyId}',
        mapper: (json) => PropertyDetailsModel.fromJson(
          Map<String, dynamic>.from(json as Map),
        ),
        fromCacheJson: PropertyDetailsModel.fromJson,
        toJson: (property) => property.toJson(),
      ),
    );
    PropertyDetailsModel? current;
    result.when((model) {
      if (model.key != 'fromCache') current = model.data;
    }, (_) {});
    if (isClosed) return;
    if (generation != AccountSession.generation) {
      setError(errorMessage: LocaleKeys.unauthorized);
      return;
    }
    final inventory = current?.rentalInventory;
    final offer = inventory?.offerById(selection.offerId);
    if (inventory?.isSupported != true ||
        offer == null ||
        current!.id != selection.propertyId ||
        (archive ? !offer.canArchive : !offer.canSetAvailability) ||
        (availability != null &&
            !const {
              'available',
              'rented',
              'unavailable',
            }.contains(availability))) {
      setError(errorMessage: LocaleKeys.rentalNotAvailable);
      return;
    }
    if (!selection.sameTermsAs(
      RentalSelection.fromOffer(
        propertyId: current!.id,
        inventory: inventory!,
        offer: offer,
      ),
    )) {
      setError(errorMessage: LocaleKeys.rentalTermsChanged);
      return;
    }
    final changed = inventory.copyWith(
      offers: [
        for (final old in inventory.offers)
          old.id == offer.id
              ? old.copyWith(
                  availability: availability,
                  archived: archive || old.archived,
                )
              : old,
      ],
    );
    if (RentalInventoryValidation.validate(
          changed,
          totalBedrooms: current!.bedrooms,
        ).isNotEmpty &&
        !archive) {
      setError(errorMessage: LocaleKeys.rentalInvalidInventory);
      return;
    }
    await executeAsyncWithBaseModel(
      // Fresh validation is retried explicitly. Reconnection must never replay
      // an occupancy/archive write without reviewing the current inventory.
      withInternetInterceptor: false,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(current!.id),
          httpRequestType: HttpRequestType.patch,
          headers: const {'X-Rental-Offers-Version': '1'},
          isFromData: true,
          body: {
            'rental_inventory': jsonEncode(
              changed.toRequestJson(
                includeMedia: capabilities.canAssociateMedia,
              ),
            ),
          },
          mapper: (json) {
            final saved = PropertyDetailsModel.fromJson(
              Map<String, dynamic>.from(json as Map),
            );
            final confirmed = saved.rentalInventory?.offerById(offer.id);
            if (saved.id != selection.propertyId ||
                confirmed == null ||
                !RentalInventoryConfirmation.matches(
                  changed,
                  saved.rentalInventory,
                  includeMedia: capabilities.canAssociateMedia,
                ) ||
                (archive && !confirmed.archived) ||
                (availability != null &&
                    confirmed.availability != availability)) {
              throw FormatException(LocaleKeys.rentalIncompatibleResponse);
            }
            return saved;
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
