import 'package:equatable/equatable.dart';
import '../enums/rental_scope.dart';
import '../rental_json.dart';
import 'rental_terms.dart';
import 'rental_accommodation_draft_details.dart';

class RentalOffer extends Equatable {
  const RentalOffer({
    this.id = '',
    this.draftKey = '',
    this.scopeValue,
    this.name = '',
    this.roomRefs = const [],
    this.bedRef = '',
    this.terms = const RentalTerms.initial(),
    this.inheritedFields = const {},
    this.availability,
    this.archived = false,
    this.revision = 0,
    this.mediaIds = const [],
    this.link = '',
    this.isSaved = false,
    this.canArchive = false,
    this.canSetAvailability = false,
    this.draftDetails = const RentalOfferDraftDetails(),
  });
  const RentalOffer.initial() : this();
  factory RentalOffer.fromJson(Map<String, dynamic> json) => RentalOffer(
    id: json['id']?.toString() ?? '',
    draftKey: json['client_key']?.toString() ?? '',
    scopeValue: json.containsKey('rental_scope')
        ? json['rental_scope']?.toString()
        : null,
    name: json['name']?.toString() ?? '',
    roomRefs: rentalStrings(json['room_ids']),
    bedRef: json['bed_id']?.toString() ?? '',
    terms: RentalTerms.fromJson(rentalMap(json['terms'])),
    inheritedFields: rentalStrings(json['inherited_fields']).toSet(),
    availability: json['availability']?.toString(),
    archived: json['archived'] == true,
    revision: rentalInt(json['revision']),
    mediaIds: rentalStrings(json['media_ids']),
    link: json['offer_link']?.toString() ?? '',
    isSaved: json['is_saved'] == true,
    canArchive: rentalMap(json['actions'])['can_archive'] == true,
    canSetAvailability:
        rentalMap(json['actions'])['can_set_availability'] == true,
  );

  factory RentalOffer.fromDraftJson(Map<String, dynamic> json) =>
      RentalOffer.fromJson(json).copyWith(
        draftDetails: RentalOfferDraftDetails.fromJson(
          rentalMap(json['local_details']),
        ),
      );
  final RentalOfferDraftDetails draftDetails;
  Map<String, dynamic> toDraftJson() => {
    ...toJson(),
    if (draftDetails.hasData) 'local_details': draftDetails.toJson(),
  };
  final String id, draftKey, name, bedRef, link;
  final String? scopeValue, availability;
  final List<String> roomRefs, mediaIds;
  final RentalTerms terms;
  final Set<String> inheritedFields;
  final bool archived, isSaved, canArchive, canSetAvailability;
  final int revision;
  RentalScope? get scope => RentalScope.fromValue(scopeValue);
  bool get hasUnknownScope => scopeValue != null && scope == null;
  bool get isAvailable => !archived && availability == 'available';
  String get reference => id.isNotEmpty ? id : draftKey;

  Map<String, dynamic> toJson() => {
    if (id.isNotEmpty) 'id': id,
    if (draftKey.isNotEmpty) 'client_key': draftKey,
    if (scopeValue != null) 'rental_scope': scopeValue,
    'name': name,
    'room_ids': roomRefs,
    'bed_id': bedRef,
    'terms': terms.toJson(),
    'inherited_fields': inheritedFields.toList(),
    'availability': availability,
    'archived': archived,
    'revision': revision,
    'media_ids': mediaIds,
    'offer_link': link,
    'is_saved': isSaved,
    'actions': {
      'can_archive': canArchive,
      'can_set_availability': canSetAvailability,
    },
  };

  /// Proposed v1 request. Scope-inapplicable references never cross the wire.
  Map<String, dynamic> toRequestJson({bool includeMedia = true}) {
    if (scope == RentalScope.roomGroup && draftDetails.hasData) {
      throw StateError(
        'Group facilities require a compatible backend contract',
      );
    }
    final overrides = terms.toJson()
      ..removeWhere((key, _) => inheritedFields.contains(key));
    return {
      if (id.isNotEmpty) 'id': id,
      if (id.isEmpty) 'client_key': draftKey,
      'rental_scope': scopeValue,
      'name': name.trim(),
      if (scope == RentalScope.room ||
          scope == RentalScope.roomGroup ||
          scope == RentalScope.bed)
        'room_ids': roomRefs,
      if (scope == RentalScope.bed) 'bed_id': bedRef,
      'term_overrides': overrides,
      'inherited_fields': inheritedFields.toList(),
      'availability': availability,
      'archived': archived,
      if (includeMedia) 'media_ids': mediaIds,
    };
  }

  RentalOffer copyWith({
    RentalOfferDraftDetails? draftDetails,
    String? id,
    String? draftKey,
    String? scopeValue,
    String? name,
    List<String>? roomRefs,
    String? bedRef,
    RentalTerms? terms,
    Set<String>? inheritedFields,
    String? availability,
    bool? archived,
    int? revision,
    List<String>? mediaIds,
    String? link,
    bool? isSaved,
    bool? canArchive,
    bool? canSetAvailability,
  }) => RentalOffer(
    draftDetails: draftDetails ?? this.draftDetails,
    id: id ?? this.id,
    draftKey: draftKey ?? this.draftKey,
    scopeValue: scopeValue ?? this.scopeValue,
    name: name ?? this.name,
    roomRefs: roomRefs ?? this.roomRefs,
    bedRef: bedRef ?? this.bedRef,
    terms: terms ?? this.terms,
    inheritedFields: inheritedFields ?? this.inheritedFields,
    availability: availability ?? this.availability,
    archived: archived ?? this.archived,
    revision: revision ?? this.revision,
    mediaIds: mediaIds ?? this.mediaIds,
    link: link ?? this.link,
    isSaved: isSaved ?? this.isSaved,
    canArchive: canArchive ?? this.canArchive,
    canSetAvailability: canSetAvailability ?? this.canSetAvailability,
  );
  @override
  List<Object?> get props => [
    id,
    draftKey,
    scopeValue,
    name,
    roomRefs,
    bedRef,
    terms,
    inheritedFields,
    availability,
    archived,
    revision,
    mediaIds,
    link,
    isSaved,
    canArchive,
    canSetAvailability,
    draftDetails,
  ];
}
