import 'package:equatable/equatable.dart';
import '../enums/rental_scope.dart';
import '../rental_json.dart';
import 'rental_inventory.dart';
import 'rental_offer.dart';
import 'rental_terms.dart';

/// Identifiable accommodation and a snapshot, never a replacement property ID.
class RentalSelection extends Equatable {
  const RentalSelection({
    this.propertyId = '',
    this.offerId = '',
    this.offerRevision = 0,
    this.scopeValue,
    this.name = '',
    this.roomIds = const [],
    this.roomNames = const [],
    this.bedId = '',
    this.bedName = '',
    this.terms = const RentalTerms.initial(),
    this.availability,
    this.archived = false,
    this.capacity,
    this.bathroomAccess = const [],
    this.offerLink = '',
  });
  const RentalSelection.initial() : this();
  factory RentalSelection.fromJson(Map<String, dynamic> json) =>
      RentalSelection(
        propertyId: json['property_id']?.toString() ?? '',
        offerId: json['offer_id']?.toString() ?? '',
        offerRevision: rentalInt(json['offer_revision']),
        scopeValue: json['rental_scope']?.toString(),
        name: json['name']?.toString() ?? '',
        roomIds: rentalStrings(json['room_ids']),
        roomNames: rentalStrings(json['room_names']),
        bedId: json['bed_id']?.toString() ?? '',
        bedName: json['bed_name']?.toString() ?? '',
        terms: RentalTerms.fromJson(rentalMap(json['terms'])),
        availability: json['availability']?.toString(),
        archived: json['archived'] == true,
        capacity: json['capacity'] == null ? null : rentalInt(json['capacity']),
        bathroomAccess: rentalStrings(json['bathroom_access']),
        offerLink: json['offer_link']?.toString() ?? '',
      );
  factory RentalSelection.fromOffer({
    required String propertyId,
    required RentalInventory inventory,
    required RentalOffer offer,
  }) {
    final rooms = offer.roomRefs.map(inventory.roomByRef).nonNulls.toList();
    final bed = rooms
        .expand((room) => room.beds)
        .where((bed) => bed.reference == offer.bedRef)
        .firstOrNull;
    return RentalSelection(
      propertyId: propertyId,
      offerId: offer.id,
      offerRevision: offer.revision,
      scopeValue: offer.scopeValue,
      name: offer.name,
      roomIds: offer.roomRefs,
      roomNames: rooms.map((room) => room.name).toList(),
      bedId: offer.bedRef,
      bedName: bed?.name ?? '',
      terms: inventory.resolved(offer).terms,
      availability: offer.availability,
      archived: offer.archived,
      capacity: rooms.isEmpty
          ? null
          : rooms.fold<int>(0, (sum, room) => sum + room.capacity),
      bathroomAccess: rooms
          .map((room) => room.bathroomAccess)
          .where((value) => value.isNotEmpty)
          .toSet()
          .toList(),
      offerLink: offer.link,
    );
  }

  /// Historical records use the server snapshot. No current-price reconstruction.
  static RentalSelection? fromRecord(Map<String, dynamic> record) {
    final snapshot = rentalMap(record['offer_snapshot']);
    final String id =
        (record['offer_id'] ?? snapshot['offer_id'])?.toString() ?? '';
    if (id.isEmpty && !record.containsKey('offer_snapshot')) return null;
    return RentalSelection.fromJson({
      'property_id':
          rentalMap(record['property'])['id'] ?? record['property_id'],
      ...snapshot,
      'offer_id': id,
    });
  }

  final String propertyId, offerId, name, bedId, bedName, offerLink;
  final String? scopeValue, availability;
  final int offerRevision;
  final int? capacity;
  final List<String> roomIds, roomNames, bathroomAccess;
  final RentalTerms terms;
  final bool archived;
  RentalScope? get scope => RentalScope.fromValue(scopeValue);
  bool get isAvailable => availability == 'available' && !archived;
  bool get canIdentify =>
      propertyId.trim().isNotEmpty &&
      offerId.trim().isNotEmpty &&
      roomIds.every((id) => id.trim().isNotEmpty) &&
      switch (scope) {
        RentalScope.entireProperty => roomIds.isEmpty && bedId.isEmpty,
        RentalScope.room =>
          roomIds.length == 1 &&
              bedId.isEmpty &&
              roomNames.length == 1 &&
              roomNames.single.trim().isNotEmpty,
        RentalScope.roomGroup =>
          roomIds.length >= 2 &&
              roomIds.toSet().length == roomIds.length &&
              bedId.isEmpty &&
              roomNames.length == roomIds.length &&
              roomNames.every((name) => name.trim().isNotEmpty),
        RentalScope.bed =>
          roomIds.length == 1 &&
              bedId.trim().isNotEmpty &&
              roomNames.length == 1 &&
              roomNames.single.trim().isNotEmpty &&
              bedName.trim().isNotEmpty &&
              (capacity ?? 0) >= 2,
        null => false,
      };
  bool sameTermsAs(RentalSelection other) =>
      propertyId == other.propertyId &&
      offerId == other.offerId &&
      offerRevision == other.offerRevision &&
      scopeValue == other.scopeValue &&
      name == other.name &&
      terms == other.terms &&
      _same(roomIds, other.roomIds) &&
      _same(roomNames, other.roomNames) &&
      bedId == other.bedId &&
      bedName == other.bedName &&
      capacity == other.capacity &&
      _same(bathroomAccess, other.bathroomAccess);
  static bool _same(List<String> a, List<String> b) =>
      a.length == b.length && a.toSet().containsAll(b);
  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'offer_id': offerId,
    'offer_revision': offerRevision,
    'rental_scope': scopeValue,
    'name': name,
    'room_ids': roomIds,
    'room_names': roomNames,
    'bed_id': bedId,
    'bed_name': bedName,
    'terms': terms.toJson(),
    'availability': availability,
    'archived': archived,
    'capacity': capacity,
    'bathroom_access': bathroomAccess,
    'offer_link': offerLink,
  };
  RentalSelection copyWith({
    String? propertyId,
    String? offerId,
    int? offerRevision,
    String? scopeValue,
    String? name,
    List<String>? roomIds,
    List<String>? roomNames,
    String? bedId,
    String? bedName,
    RentalTerms? terms,
    String? availability,
    bool? archived,
    int? capacity,
    List<String>? bathroomAccess,
    String? offerLink,
  }) => RentalSelection(
    propertyId: propertyId ?? this.propertyId,
    offerId: offerId ?? this.offerId,
    offerRevision: offerRevision ?? this.offerRevision,
    scopeValue: scopeValue ?? this.scopeValue,
    name: name ?? this.name,
    roomIds: roomIds ?? this.roomIds,
    roomNames: roomNames ?? this.roomNames,
    bedId: bedId ?? this.bedId,
    bedName: bedName ?? this.bedName,
    terms: terms ?? this.terms,
    availability: availability ?? this.availability,
    archived: archived ?? this.archived,
    capacity: capacity ?? this.capacity,
    bathroomAccess: bathroomAccess ?? this.bathroomAccess,
    offerLink: offerLink ?? this.offerLink,
  );
  @override
  List<Object?> get props => [
    propertyId,
    offerId,
    offerRevision,
    scopeValue,
    name,
    roomIds,
    roomNames,
    bedId,
    bedName,
    terms,
    availability,
    archived,
    capacity,
    bathroomAccess,
    offerLink,
  ];
}
