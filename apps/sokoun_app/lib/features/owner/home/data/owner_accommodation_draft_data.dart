import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_offer.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_draft_editing.dart';
import 'models/owner_add_property_content.dart';

/// Composition changes reuse the existing inventory; unused local rooms remain
/// recoverable in the draft and are excluded from submission/validation.
abstract final class OwnerAccommodationDraftData {
  static OwnerAddPropertyFormState chooseScope(
    OwnerAddPropertyFormState form,
    RentalScope scope,
  ) {
    var inventory = RentalDraftEditing.chooseScope(form.rentalInventory, scope);
    if (RentalDraftEditing.hasPersistedOffers(inventory) &&
        (scope == RentalScope.entireProperty ||
            inventory.mode == 'whole' ||
            form.selectedOffer?.id.isNotEmpty == true)) {
      return form;
    }
    var offer =
        inventory.offers
            .where((o) => o.reference == form.selectedOfferRef)
            .firstOrNull ??
        inventory.offers.firstOrNull;
    if (offer == null) {
      return form.copyWith(rentalInventory: inventory);
    }
    if (offer.id.isNotEmpty) {
      return form;
    }
    offer = RentalDraftEditing.changeScope(offer, scope);
    inventory = replaceOffer(inventory, offer);
    inventory = prepareAccommodation(inventory, offer);
    return form.copyWith(
      rentalInventory: inventory,
      selectedOfferRef: offer.reference,
    );
  }

  static RentalInventory prepareAccommodation(
    RentalInventory inventory,
    RentalOffer offer,
  ) {
    if (offer.scope == RentalScope.entireProperty || offer.scope == null) {
      return inventory;
    }
    final rooms = [...inventory.rooms];
    final refs = [...offer.roomRefs];
    final minimum = offer.scope == RentalScope.roomGroup ? 2 : 1;
    while (refs.length < minimum) {
      final room = RentalRoom(draftKey: RentalDraftEditing.key());
      rooms.add(room);
      refs.add(room.reference);
    }
    if (offer.scope != RentalScope.roomGroup && refs.length > 1) {
      refs.removeRange(1, refs.length);
    }
    var bedRef = offer.bedRef;
    if (offer.scope == RentalScope.bed && bedRef.isEmpty) {
      final index = rooms.indexWhere((room) => room.reference == refs.single);
      if (index >= 0) {
        final bed = RentalBed(draftKey: RentalDraftEditing.key());
        rooms[index] = rooms[index].copyWith(beds: [...rooms[index].beds, bed]);
        bedRef = bed.reference;
      }
    }
    return replaceOffer(
      inventory.copyWith(rooms: rooms),
      offer.copyWith(roomRefs: refs, bedRef: bedRef),
    );
  }

  static OwnerAddPropertyFormState addIndependentOffer(
    OwnerAddPropertyFormState form,
    RentalScope scope,
  ) {
    final inventory = form.rentalInventory;
    if (inventory == null ||
        !inventory.isPartial ||
        scope == RentalScope.entireProperty) {
      return form;
    }
    final offer = RentalDraftEditing.newOffer(scope);
    return form.copyWith(
      selectedOfferRef: offer.reference,
      rentalInventory: prepareAccommodation(
        inventory.copyWith(offers: [...inventory.offers, offer]),
        offer,
      ),
    );
  }

  static RentalInventory replaceOffer(
    RentalInventory inventory,
    RentalOffer offer,
  ) => inventory.copyWith(
    offers: [
      for (final current in inventory.offers)
        current.reference == offer.reference ? offer : current,
    ],
  );

  static RentalInventory replaceRoom(
    RentalInventory inventory,
    RentalRoom room,
  ) => inventory.copyWith(
    rooms: [
      for (final current in inventory.rooms)
        current.reference == room.reference ? room : current,
    ],
  );

  static RentalInventory addRoom(RentalInventory inventory, RentalOffer offer) {
    final room = RentalRoom(draftKey: RentalDraftEditing.key());
    return replaceOffer(
      inventory.copyWith(rooms: [...inventory.rooms, room]),
      offer.copyWith(
        roomRefs: offer.scope == RentalScope.roomGroup
            ? [...offer.roomRefs, room.reference]
            : [room.reference],
        bedRef: '',
      ),
    );
  }

  static List<String> lines(String text) => text
      .split('\n')
      .map((v) => v.trim())
      .where((v) => v.isNotEmpty)
      .toSet()
      .toList();
}
