import 'enums/rental_scope.dart';
import 'models/rental_inventory.dart';
import 'models/rental_terms.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';

/// A v1 write succeeds only when the server confirms what was submitted.
abstract final class RentalInventoryConfirmation {
  static bool matches(
    RentalInventory submitted,
    RentalInventory? stored, {
    bool includeMedia = true,
  }) {
    if (stored == null ||
        !stored.isSupported ||
        stored.mode != submitted.mode ||
        stored.offers.length != submitted.offers.length ||
        stored.rooms.length != submitted.rooms.length ||
        (includeMedia &&
            !_ids(submitted.sharedMediaIds, stored.sharedMediaIds))) {
      return false;
    }
    final rooms = <String, String>{};
    final beds = <String, String>{};
    for (final room in submitted.rooms) {
      final saved = stored.rooms
          .where(
            (candidate) => room.id.isNotEmpty
                ? candidate.id == room.id
                : candidate.draftKey == room.draftKey,
          )
          .firstOrNull;
      if (saved == null ||
          saved.id.isEmpty ||
          saved.name.trim() != room.name.trim() ||
          saved.capacity != room.capacity ||
          saved.bathroomAccess != room.bathroomAccess ||
          saved.description.trim() != room.description.trim() ||
          saved.beds.length != room.beds.length ||
          (includeMedia && !_ids(room.mediaIds, saved.mediaIds))) {
        return false;
      }
      rooms[room.reference] = saved.id;
      for (final bed in room.beds) {
        final savedBed = saved.beds
            .where(
              (candidate) => bed.id.isNotEmpty
                  ? candidate.id == bed.id
                  : candidate.draftKey == bed.draftKey,
            )
            .firstOrNull;
        if (savedBed == null ||
            savedBed.id.isEmpty ||
            savedBed.name.trim() != bed.name.trim() ||
            (includeMedia && !_ids(bed.mediaIds, savedBed.mediaIds))) {
          return false;
        }
        beds[bed.reference] = savedBed.id;
      }
    }
    for (final offer in submitted.offers) {
      final saved = stored.offers
          .where(
            (candidate) => offer.id.isNotEmpty
                ? candidate.id == offer.id
                : candidate.draftKey == offer.draftKey,
          )
          .firstOrNull;
      if (saved == null ||
          saved.id.isEmpty ||
          saved.name.trim() != offer.name.trim() ||
          saved.scopeValue != offer.scopeValue ||
          saved.availability != offer.availability ||
          saved.archived != offer.archived ||
          !saved.inheritedFields.containsAll(offer.inheritedFields) ||
          saved.inheritedFields.length != offer.inheritedFields.length ||
          (includeMedia && !_ids(offer.mediaIds, saved.mediaIds)) ||
          !_terms(
            submitted.resolved(offer).terms,
            stored.resolved(saved).terms,
          )) {
        return false;
      }
      if (offer.scope != RentalScope.entireProperty) {
        final expectedRooms = offer.roomRefs
            .map((ref) => rooms[ref] ?? ref)
            .toSet();
        if (saved.roomRefs.length != expectedRooms.length ||
            !expectedRooms.containsAll(saved.roomRefs)) {
          return false;
        }
      }
      if (offer.scope == RentalScope.bed &&
          saved.bedRef != (beds[offer.bedRef] ?? offer.bedRef)) {
        return false;
      }
    }
    return true;
  }

  static bool _ids(List<String> a, List<String> b) =>
      a.length == b.length && a.toSet().containsAll(b);

  static bool _terms(RentalTerms a, RentalTerms b) =>
      EgyptianPound.parseAmount(a.price) ==
          EgyptianPound.parseAmount(b.price) &&
      a.pricePeriod == b.pricePeriod &&
      a.minimumMonths == b.minimumMonths &&
      a.deposit.trim() == b.deposit.trim() &&
      a.suitableFor == b.suitableFor &&
      a.description.trim() == b.description.trim() &&
      a.smokingAllowed == b.smokingAllowed &&
      a.rules.length == b.rules.length &&
      a.rules.toSet().containsAll(b.rules);
}
