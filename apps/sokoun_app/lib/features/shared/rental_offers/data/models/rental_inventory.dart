import 'package:equatable/equatable.dart';
import '../rental_json.dart';
import 'rental_offer.dart';
import 'rental_room.dart';
import 'rental_terms.dart';
import 'rental_accommodation_draft_details.dart';

class RentalInventory extends Equatable {
  const RentalInventory({
    this.schemaVersion = 1,
    this.mode,
    this.revision = 0,
    this.rooms = const [],
    this.offers = const [],
    this.defaults = const RentalTerms.initial(),
    this.sharedMediaIds = const [],
    this.parkedOffers = const [],
    this.draftDetails = const RentalSharedDraftDetails(),
  });
  const RentalInventory.initial() : this();
  factory RentalInventory.fromJson(Map<String, dynamic> json) =>
      RentalInventory(
        schemaVersion: rentalInt(json['schema_version']),
        mode: json['mode']?.toString(),
        revision: rentalInt(json['revision']),
        rooms: rentalMaps(
          json['rooms'],
        ).map(RentalRoom.fromJson).toList(growable: false),
        offers: rentalMaps(
          json['offers'],
        ).map(RentalOffer.fromJson).toList(growable: false),
        defaults: RentalTerms.fromJson(rentalMap(json['shared_defaults'])),
        sharedMediaIds: rentalStrings(json['shared_media_ids']),
        parkedOffers: rentalMaps(
          json['parked_offers'],
        ).map(RentalOffer.fromJson).toList(growable: false),
      );
  factory RentalInventory.fromDraftJson(Map<String, dynamic> json) =>
      RentalInventory.fromJson(json).copyWith(
        rooms: rentalMaps(json['rooms']).map(RentalRoom.fromDraftJson).toList(),
        offers: rentalMaps(
          json['offers'],
        ).map(RentalOffer.fromDraftJson).toList(),
        parkedOffers: rentalMaps(
          json['parked_offers'],
        ).map(RentalOffer.fromDraftJson).toList(),
        draftDetails: RentalSharedDraftDetails.fromJson(
          rentalMap(json['local_details']),
        ),
      );
  final RentalSharedDraftDetails draftDetails;
  bool get hasLocalOnlyDetails =>
      draftDetails.hasData ||
      offers.any(
        (offer) =>
            offer.scopeValue == 'room_group' && offer.draftDetails.hasData,
      ) ||
      rooms.any(
        (room) =>
            room.draftDetails.hasData ||
            room.beds.any((bed) => bed.draftDetails.hasData),
      );
  final int schemaVersion, revision;
  final String? mode;
  final List<RentalRoom> rooms;
  final List<RentalOffer> offers, parkedOffers;
  final RentalTerms defaults;
  final List<String> sharedMediaIds;

  /// A present but malformed/future inventory must not fall back to legacy.
  static RentalInventory? read(Map<String, dynamic> json) {
    if (!json.containsKey('rental_inventory')) {
      return json['rental_schema_version'] != null
          ? RentalInventory(
              schemaVersion:
                  int.tryParse('${json['rental_schema_version']}') ?? 0,
            )
          : null;
    }
    final value = json['rental_inventory'];
    // The deployed API explicitly uses this empty projection for legacy listings.
    if (value is Map &&
        value.length == 1 &&
        value['offers'] is List &&
        (value['offers'] as List).isEmpty &&
        json['rental_schema_version'] == null) {
      return null;
    }
    return value is Map
        ? RentalInventory.fromJson(Map<String, dynamic>.from(value))
        : const RentalInventory(schemaVersion: 0);
  }

  bool get isSupported =>
      schemaVersion == 1 && (mode == 'whole' || mode == 'partial');
  bool get isPartial => mode == 'partial';
  RentalOffer? offerById(String id) =>
      offers.where((offer) => offer.id == id && id.isNotEmpty).firstOrNull;
  RentalRoom? roomByRef(String ref) =>
      rooms.where((room) => room.reference == ref).firstOrNull;
  RentalOffer resolved(RentalOffer offer) => offer.copyWith(
    terms: offer.terms.resolve(defaults, offer.inheritedFields),
  );
  List<String> mediaFor(RentalOffer offer) => {
    ...offer.mediaIds,
    for (final ref in offer.roomRefs) ...?roomByRef(ref)?.mediaIds,
    for (final ref in offer.roomRefs)
      ...?roomByRef(ref)?.beds
          .where((bed) => bed.reference == offer.bedRef)
          .firstOrNull
          ?.mediaIds,
  }.toList(growable: false);
  Map<String, dynamic> toJson() => {
    'schema_version': schemaVersion,
    'mode': mode,
    'revision': revision,
    'rooms': rooms.map((room) => room.toJson()).toList(),
    'offers': offers.map((offer) => offer.toJson()).toList(),
    'shared_defaults': defaults.toDefaultsJson(),
    'shared_media_ids': sharedMediaIds,
  };
  Map<String, dynamic> toDraftJson() => {
    ...toJson(),
    'rooms': rooms.map((room) => room.toDraftJson()).toList(),
    if (draftDetails.hasData) 'local_details': draftDetails.toJson(),
    'offers': offers.map((offer) => offer.toDraftJson()).toList(),
    'parked_offers': parkedOffers.map((offer) => offer.toDraftJson()).toList(),
  };
  Map<String, dynamic> toRequestJson({bool includeMedia = true}) {
    if (hasLocalOnlyDetails) {
      throw StateError(
        'Accommodation details require a compatible backend contract',
      );
    }
    return {
      'schema_version': schemaVersion,
      'mode': mode,
      'expected_revision': revision,
      'rooms': rooms.map((room) {
        final data = room.toJson();
        if (!includeMedia) {
          data.remove('media_ids');
          for (final bed in data['beds'] as List) {
            (bed as Map).remove('media_ids');
          }
        }
        return data;
      }).toList(),
      'offers': offers
          .map((offer) => offer.toRequestJson(includeMedia: includeMedia))
          .toList(),
      'shared_defaults': defaults.toDefaultsJson(),
      if (includeMedia) 'shared_media_ids': sharedMediaIds,
    };
  }

  RentalInventory copyWith({
    RentalSharedDraftDetails? draftDetails,
    int? schemaVersion,
    String? mode,
    int? revision,
    List<RentalRoom>? rooms,
    List<RentalOffer>? offers,
    RentalTerms? defaults,
    List<String>? sharedMediaIds,
    List<RentalOffer>? parkedOffers,
  }) => RentalInventory(
    draftDetails: draftDetails ?? this.draftDetails,
    schemaVersion: schemaVersion ?? this.schemaVersion,
    mode: mode ?? this.mode,
    revision: revision ?? this.revision,
    rooms: rooms ?? this.rooms,
    offers: offers ?? this.offers,
    defaults: defaults ?? this.defaults,
    sharedMediaIds: sharedMediaIds ?? this.sharedMediaIds,
    parkedOffers: parkedOffers ?? this.parkedOffers,
  );
  @override
  List<Object?> get props => [
    schemaVersion,
    mode,
    revision,
    rooms,
    offers,
    defaults,
    sharedMediaIds,
    parkedOffers,
    draftDetails,
  ];
}
