import 'enums/rental_scope.dart';
import 'models/rental_inventory.dart';
import 'models/rental_terms.dart';

enum RentalInventoryIssue {
  unsupported,
  roomIdentity,
  bedIdentity,
  capacity,
  noOffers,
  offerIdentity,
  selection,
  roomGroup,
  overlap,
  mode,
  terms,
  availability,
  roomArea,
}

abstract final class RentalInventoryValidation {
  static Set<RentalInventoryIssue> validate(
    RentalInventory inventory, {
    int? totalBedrooms,
    bool includeTerms = true,
  }) {
    final issues = <RentalInventoryIssue>{};
    if (!inventory.isSupported) issues.add(RentalInventoryIssue.unsupported);
    final roomIds = <String>{};
    final bedIds = <String>{};
    if (totalBedrooms != null && inventory.rooms.length > totalBedrooms) {
      issues.add(RentalInventoryIssue.capacity);
    }
    for (final room in inventory.rooms) {
      if (!room.draftDetails.isValid) issues.add(RentalInventoryIssue.roomArea);
      if (room.reference.isEmpty ||
          room.name.trim().isEmpty ||
          !roomIds.add(room.reference)) {
        issues.add(RentalInventoryIssue.roomIdentity);
      }
      if (room.capacity < 1 || room.beds.length > room.capacity) {
        issues.add(RentalInventoryIssue.capacity);
      }
      for (final bed in room.beds) {
        if (bed.reference.isEmpty ||
            bed.name.trim().isEmpty ||
            !bedIds.add(bed.reference)) {
          issues.add(RentalInventoryIssue.bedIdentity);
        }
      }
    }
    final active = inventory.offers.where((offer) => !offer.archived).toList();
    if (active.isEmpty) issues.add(RentalInventoryIssue.noOffers);
    final offerIds = <String>{};
    final wholeRooms = <String>{};
    final bedRooms = <String>{};
    final offeredBeds = <String>{};
    for (final offer in active) {
      if (offer.reference.isEmpty || !offerIds.add(offer.reference)) {
        issues.add(RentalInventoryIssue.offerIdentity);
      }
      if (!RentalTerms.inheritedFields.containsAll(offer.inheritedFields) ||
          (includeTerms && !inventory.resolved(offer).terms.isValid)) {
        issues.add(RentalInventoryIssue.terms);
      }
      if (!const {
        'available',
        'rented',
        'unavailable',
      }.contains(offer.availability)) {
        issues.add(RentalInventoryIssue.availability);
      }
      final scope = offer.scope;
      if (scope == null) {
        issues.add(RentalInventoryIssue.unsupported);
        continue;
      }
      if (scope == RentalScope.entireProperty) {
        if (inventory.isPartial || active.length != 1) {
          issues.add(RentalInventoryIssue.mode);
        }
        continue;
      }
      if (!inventory.isPartial) issues.add(RentalInventoryIssue.mode);
      final refs = offer.roomRefs.toSet();
      if (refs.length != offer.roomRefs.length ||
          refs.any((ref) => !roomIds.contains(ref))) {
        issues.add(RentalInventoryIssue.selection);
      }
      if (scope == RentalScope.roomGroup && refs.length < 2) {
        issues.add(RentalInventoryIssue.roomGroup);
      }
      if ((scope == RentalScope.room || scope == RentalScope.bed) &&
          refs.length != 1) {
        issues.add(RentalInventoryIssue.selection);
      }
      if (scope == RentalScope.bed) {
        final room = refs.length == 1 ? inventory.roomByRef(refs.single) : null;
        if (room == null ||
            room.capacity < 2 ||
            !room.beds.any((bed) => bed.reference == offer.bedRef)) {
          issues.add(RentalInventoryIssue.selection);
        }
        if (!offeredBeds.add(offer.bedRef)) {
          issues.add(RentalInventoryIssue.overlap);
        }
        bedRooms.addAll(refs);
      } else {
        for (final ref in refs) {
          if (!wholeRooms.add(ref)) issues.add(RentalInventoryIssue.overlap);
        }
      }
    }
    if (wholeRooms.intersection(bedRooms).isNotEmpty) {
      issues.add(RentalInventoryIssue.overlap);
    }
    return issues;
  }
}
