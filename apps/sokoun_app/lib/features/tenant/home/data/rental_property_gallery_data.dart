import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'models/property_details_model.dart';

enum RentalPhotoContext { accommodation, parentRoom, shared, property }

class RentalPropertyGallery extends Equatable {
  const RentalPropertyGallery({
    this.images = const [],
    this.contexts = const [],
  });
  final List<PropertyImageModel> images;
  final List<RentalPhotoContext> contexts;
  bool get hasGeneralPhotos => contexts.contains(RentalPhotoContext.property);

  factory RentalPropertyGallery.fromProperty(
    PropertyDetailsModel property, {
    RentalSelection? selection,
  }) {
    final inventory = property.rentalInventory;
    final offer = inventory?.offerById(selection?.offerId ?? '');
    final isWhole = offer?.scope == RentalScope.entireProperty;
    final selected = <String>{
      ...?offer?.mediaIds,
      if (offer != null && inventory != null)
        for (final ref in offer.roomRefs)
          if (offer.scope == RentalScope.bed)
            ...?inventory
                .roomByRef(ref)
                ?.beds
                .where((bed) => bed.reference == offer.bedRef)
                .firstOrNull
                ?.mediaIds
          else
            ...?inventory.roomByRef(ref)?.mediaIds,
    };
    final parents = <String>{
      if (offer?.scope == RentalScope.bed && inventory != null)
        for (final ref in offer!.roomRefs)
          ...?inventory.roomByRef(ref)?.mediaIds,
    };
    final shared = inventory?.sharedMediaIds.toSet() ?? <String>{};
    final associated = <String>{
      if (inventory != null) ...[
        for (final room in inventory.rooms) ...[
          ...room.mediaIds,
          for (final bed in room.beds) ...bed.mediaIds,
        ],
        for (final candidate in inventory.offers) ...candidate.mediaIds,
      ],
    };
    final eligible = <PropertyImageModel>[];
    final contexts = <RentalPhotoContext>[];
    final hasSelectedPhotos = property.galleryImages.any(
      (image) => selected.contains(image.id) || parents.contains(image.id),
    );
    for (final image in property.galleryImages) {
      final context = shared.contains(image.id)
          ? RentalPhotoContext.shared
          : selected.contains(image.id)
          ? RentalPhotoContext.accommodation
          : parents.contains(image.id)
          ? RentalPhotoContext.parentRoom
          : RentalPhotoContext.property;
      if (inventory == null ||
          offer == null ||
          isWhole ||
          context != RentalPhotoContext.property ||
          (!hasSelectedPhotos && !associated.contains(image.id))) {
        eligible.add(image);
        contexts.add(context);
      }
    }
    return RentalPropertyGallery(images: eligible, contexts: contexts);
  }

  @override
  List<Object?> get props => [images, contexts];
}
