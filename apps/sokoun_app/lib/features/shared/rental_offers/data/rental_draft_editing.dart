import 'package:uuid/uuid.dart';
import 'enums/rental_scope.dart';
import 'models/rental_inventory.dart';
import 'models/rental_offer.dart';

/// Client keys are draft references only. The server assigns permanent IDs.
abstract final class RentalDraftEditing {
  static String key() => const Uuid().v4();
  static RentalOffer newOffer(RentalScope scope) => RentalOffer(
    draftKey: key(),
    scopeValue: scope.value,
    availability: 'available',
  );

  static RentalInventory chooseScope(
    RentalInventory? previous,
    RentalScope scope,
  ) {
    final partial = scope != RentalScope.entireProperty;
    final old = previous ?? const RentalInventory();
    // Replacing persisted accommodation requires an authoritative transition
    // contract. Local draft mode switches cannot archive requests or leases.
    if (hasPersistedOffers(old)) return old;
    if (old.mode == (partial ? 'partial' : 'whole')) {
      if (partial && old.offers.length == 1 && old.offers.single.id.isEmpty) {
        return old.copyWith(offers: [changeScope(old.offers.single, scope)]);
      }
      if (partial && old.offers.isEmpty) {
        return old.copyWith(offers: [newOffer(scope)]);
      }
      return old;
    }
    final restored = old.parkedOffers
        .where(
          (offer) => (offer.scope != RentalScope.entireProperty) == partial,
        )
        .toList();
    return old.copyWith(
      mode: partial ? 'partial' : 'whole',
      offers: restored.isEmpty ? [newOffer(scope)] : restored,
      parkedOffers: old.offers,
    );
  }

  static bool hasPersistedOffers(RentalInventory inventory) => [
    ...inventory.offers,
    ...inventory.parkedOffers,
  ].any((offer) => offer.id.isNotEmpty);

  static RentalInventory? withoutMedia(RentalInventory? inventory, String id) {
    if (inventory == null || id.isEmpty) return inventory;
    List<String> remove(List<String> ids) =>
        ids.where((value) => value != id).toList(growable: false);
    return inventory.copyWith(
      sharedMediaIds: remove(inventory.sharedMediaIds),
      draftDetails: inventory.draftDetails.copyWith(
        photoRefs: remove(inventory.draftDetails.photoRefs),
      ),
      rooms: [
        for (final room in inventory.rooms)
          room.copyWith(
            mediaIds: remove(room.mediaIds),
            draftDetails: room.draftDetails.copyWith(
              photoRefs: remove(room.draftDetails.photoRefs),
            ),
            beds: [
              for (final bed in room.beds)
                bed.copyWith(
                  mediaIds: remove(bed.mediaIds),
                  draftDetails: bed.draftDetails.copyWith(
                    photoRefs: remove(bed.draftDetails.photoRefs),
                  ),
                ),
            ],
          ),
      ],
      offers: [
        for (final offer in inventory.offers)
          offer.copyWith(mediaIds: remove(offer.mediaIds)),
      ],
      parkedOffers: [
        for (final offer in inventory.parkedOffers)
          offer.copyWith(mediaIds: remove(offer.mediaIds)),
      ],
    );
  }

  /// Terms survive a draft scope change; incompatible accommodation does not.
  static RentalOffer changeScope(RentalOffer offer, RentalScope scope) {
    if (offer.scope == scope) return offer;
    return offer.copyWith(
      scopeValue: scope.value,
      roomRefs:
          scope == RentalScope.entireProperty ||
              (scope != RentalScope.roomGroup && offer.roomRefs.length != 1)
          ? const []
          : offer.roomRefs,
      bedRef: '',
      mediaIds: const [],
    );
  }

  static RentalOffer selectRoom(
    RentalOffer offer, {
    required String roomRef,
    required bool selected,
  }) => offer.copyWith(
    roomRefs: offer.scope == RentalScope.roomGroup
        ? ([...offer.roomRefs]
            ..remove(roomRef)
            ..addAll(selected ? [roomRef] : const []))
        : selected
        ? [roomRef]
        : const [],
    bedRef: '',
    mediaIds: const [],
  );
}
