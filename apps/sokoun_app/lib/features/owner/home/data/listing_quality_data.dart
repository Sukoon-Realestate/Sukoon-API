import 'enums/listing_quality_check.dart';
import 'models/owner_add_property_content.dart';

abstract final class ListingQualityData {
  /// Suggestions only: publication requirements remain in the form validators.
  static Map<ListingQualityCheck, bool> evaluate(
    OwnerAddPropertyFormState form,
  ) => {
    ListingQualityCheck.photos:
        form.photoCount >= OwnerAddPropertyContent.minimumPhotoCount,
    ListingQualityCheck.location: form.isLocationSelected,
    ListingQualityCheck.description: form.isPartialOffering
        ? form.rentalInventory!.offers
              .where((offer) => !offer.archived)
              .every(
                (offer) =>
                    form.rentalInventory!
                        .resolved(offer)
                        .terms
                        .description
                        .trim()
                        .length >=
                    40,
              )
        : form.description.trim().length >= 40,
    ListingQualityCheck.deposit: form.isPartialOffering
        ? form.rentalInventory!.offers
              .where((offer) => !offer.archived)
              .every(
                (offer) =>
                    form.rentalInventory!
                        .resolved(offer)
                        .terms
                        .deposit
                        .isNotEmpty &&
                    form.rentalInventory!.resolved(offer).terms.hasValidDeposit,
              )
        : form.deposit.trim().isNotEmpty && form.isDepositReady,
    ListingQualityCheck.captions:
        form.photoDrafts.isNotEmpty &&
        form.photoDrafts.every(
          (photo) =>
              photo.name.trim().isNotEmpty ||
              photo.description.trim().isNotEmpty,
        ),
    ListingQualityCheck.video: form.isVideoReady,
  };
}
