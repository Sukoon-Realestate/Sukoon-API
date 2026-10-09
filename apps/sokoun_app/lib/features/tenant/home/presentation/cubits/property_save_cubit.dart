import 'favorite_coordinator.dart';
import '../../data/models/favorite_target.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/main_view/data/workspace_counts_refresh_bus.dart';

class PropertySaveCubit extends AsyncCubit<bool> {
  PropertySaveCubit({this.capabilities = RentalOfferCapabilities.configured})
    : super(false);
  final RentalOfferCapabilities capabilities;

  Future<void> saveProperty({
    required String propertyId,
    RentalSelection? selection,
    bool hasRentalOffers = false,
    required void Function(String msg) onError,
  }) async {
    await _updateSavedState(
      propertyId: propertyId,
      selection: selection,
      hasRentalOffers: hasRentalOffers,
      isSaved: true,
      onError: onError,
    );
  }

  Future<void> unsaveProperty({
    required String propertyId,
    RentalSelection? selection,
    bool hasRentalOffers = false,
    required void Function(String msg) onError,
  }) async {
    await _updateSavedState(
      propertyId: propertyId,
      selection: selection,
      hasRentalOffers: hasRentalOffers,
      isSaved: false,
      onError: onError,
    );
  }

  Future<void> _updateSavedState({
    required String propertyId,
    RentalSelection? selection,
    bool hasRentalOffers = false,
    required bool isSaved,
    required void Function(String msg) onError,
  }) async {
    if (isClosed) {
      return;
    }
    if ((hasRentalOffers || selection != null) &&
        (!capabilities.canFavorite ||
            selection?.canIdentify != true ||
            selection?.propertyId != propertyId)) {
      final message = LocaleKeys.rentalUnavailableCapability;
      setError();
      updateErrorMessage(message);
      onError(message);
      return;
    }
    final target = FavoriteTarget(propertyId, selection?.offerId);
    await executeAsyncWithBaseModel(
      operation: () => FavoriteCoordinator.instance.request(
        target: target,
        desired: isSaved,
        send: (desired) => baseCrudUseCase.call(
          CrudBaseParmas<bool>(
            api: desired
                ? ApiConstants.saveProperty(propertyId)
                : ApiConstants.unsaveProperty(propertyId),
            httpRequestType: desired
                ? HttpRequestType.post
                : HttpRequestType.delete,
            body: selection == null ? null : {'offer_id': selection.offerId},
            mapper: (json) {
              if (selection != null &&
                  (json is! Map ||
                      json['offer_id']?.toString() != selection.offerId ||
                      json['is_saved'] != desired)) {
                throw FormatException(LocaleKeys.rentalIncompatibleResponse);
              }
              return desired;
            },
          ),
        ),
      ),
      onSuccess: (_) => WorkspaceCountsRefreshBus.refresh(),
      onError: onError,
    );
  }
}
