import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'models/rental_selection.dart';

class RentalOfferReadData {
  const RentalOfferReadData(this.useCase);
  final BaseCrudUseCase useCase;

  Future<RentalSelection> freshSelection(RentalSelection selected) async {
    final generation = AccountSession.generation;
    final result = await useCase.call(
      CrudBaseParmas<PropertyDetailsModel>(
        api: ApiConstants.propertyDetails(selected.propertyId),
        httpRequestType: HttpRequestType.get,
        cacheKey: 'property_details_${selected.propertyId}',
        mapper: (json) => PropertyDetailsModel.fromJson(
          Map<String, dynamic>.from(json as Map),
        ),
        fromCacheJson: PropertyDetailsModel.fromJson,
        toJson: (model) => model.toJson(),
      ),
    );
    if (generation != AccountSession.generation) {
      throw StateError(LocaleKeys.unauthorized);
    }
    RentalSelection? fresh;
    String? error;
    result.when((model) {
      if (model.key == 'fromCache') {
        error = LocaleKeys.checkInternet;
        return;
      }
      final inventory = model.data.rentalInventory;
      final offer = inventory?.offerById(selected.offerId);
      if (model.data.id != selected.propertyId ||
          inventory?.isSupported != true ||
          offer == null ||
          !offer.isAvailable ||
          offer.scope == null) {
        error = LocaleKeys.rentalNotAvailable;
        return;
      }
      fresh = RentalSelection.fromOffer(
        propertyId: model.data.id,
        inventory: inventory!,
        offer: offer,
      );
    }, (failure) => error = failure.message);
    if (fresh == null) throw StateError(error ?? LocaleKeys.rentalNotAvailable);
    return fresh!;
  }
}
