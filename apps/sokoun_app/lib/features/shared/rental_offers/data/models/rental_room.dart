import 'package:equatable/equatable.dart';
import '../rental_json.dart';
import 'rental_accommodation_draft_details.dart';

class RentalBed extends Equatable {
  const RentalBed({
    this.id = '',
    this.draftKey = '',
    this.name = '',
    this.mediaIds = const [],
    this.draftDetails = const RentalBedDraftDetails(),
  });
  const RentalBed.initial() : this();
  factory RentalBed.fromJson(Map<String, dynamic> json) => RentalBed(
    id: json['id']?.toString() ?? '',
    draftKey: json['client_key']?.toString() ?? '',
    name: json['name']?.toString() ?? '',
    mediaIds: rentalStrings(json['media_ids']),
  );
  factory RentalBed.fromDraftJson(Map<String, dynamic> json) =>
      RentalBed.fromJson(json).copyWith(
        draftDetails: RentalBedDraftDetails.fromJson(
          rentalMap(json['local_details']),
        ),
      );
  final RentalBedDraftDetails draftDetails;
  final String id, draftKey, name;
  final List<String> mediaIds;
  String get reference => id.isNotEmpty ? id : draftKey;
  Map<String, dynamic> toJson() => {
    if (id.isNotEmpty) 'id': id,
    if (draftKey.isNotEmpty) 'client_key': draftKey,
    'name': name.trim(),
    'media_ids': mediaIds,
  };
  Map<String, dynamic> toDraftJson() => {
    ...toJson(),
    if (draftDetails.hasData) 'local_details': draftDetails.toJson(),
  };
  RentalBed copyWith({
    RentalBedDraftDetails? draftDetails,
    String? id,
    String? draftKey,
    String? name,
    List<String>? mediaIds,
  }) => RentalBed(
    draftDetails: draftDetails ?? this.draftDetails,
    id: id ?? this.id,
    draftKey: draftKey ?? this.draftKey,
    name: name ?? this.name,
    mediaIds: mediaIds ?? this.mediaIds,
  );
  @override
  List<Object?> get props => [id, draftKey, name, mediaIds, draftDetails];
}

class RentalRoom extends Equatable {
  const RentalRoom({
    this.id = '',
    this.draftKey = '',
    this.name = '',
    this.capacity = 0,
    this.bathroomAccess = '',
    this.description = '',
    this.beds = const [],
    this.mediaIds = const [],
    this.draftDetails = const RentalRoomDraftDetails(),
  });
  const RentalRoom.initial() : this();
  factory RentalRoom.fromJson(Map<String, dynamic> json) => RentalRoom(
    id: json['id']?.toString() ?? '',
    draftKey: json['client_key']?.toString() ?? '',
    name: json['name']?.toString() ?? '',
    capacity: rentalInt(json['capacity']),
    bathroomAccess: json['bathroom_access']?.toString() ?? '',
    description: json['description']?.toString() ?? '',
    beds: rentalMaps(
      json['beds'],
    ).map(RentalBed.fromJson).toList(growable: false),
    mediaIds: rentalStrings(json['media_ids']),
  );
  factory RentalRoom.fromDraftJson(Map<String, dynamic> json) =>
      RentalRoom.fromJson(json).copyWith(
        draftDetails: RentalRoomDraftDetails.fromJson(
          rentalMap(json['local_details']),
        ),
        beds: rentalMaps(json['beds']).map(RentalBed.fromDraftJson).toList(),
      );
  final RentalRoomDraftDetails draftDetails;
  final String id, draftKey, name, bathroomAccess, description;
  final int capacity;
  final List<RentalBed> beds;
  final List<String> mediaIds;
  String get reference => id.isNotEmpty ? id : draftKey;
  Map<String, dynamic> toJson() => {
    if (id.isNotEmpty) 'id': id,
    if (draftKey.isNotEmpty) 'client_key': draftKey,
    'name': name.trim(),
    'capacity': capacity,
    'bathroom_access': bathroomAccess,
    'description': description.trim(),
    'beds': beds.map((bed) => bed.toJson()).toList(),
    'media_ids': mediaIds,
  };
  Map<String, dynamic> toDraftJson() => {
    ...toJson(),
    'beds': beds.map((bed) => bed.toDraftJson()).toList(),
    if (draftDetails.hasData) 'local_details': draftDetails.toJson(),
  };
  RentalRoom copyWith({
    RentalRoomDraftDetails? draftDetails,
    String? id,
    String? draftKey,
    String? name,
    int? capacity,
    String? bathroomAccess,
    String? description,
    List<RentalBed>? beds,
    List<String>? mediaIds,
  }) => RentalRoom(
    draftDetails: draftDetails ?? this.draftDetails,
    id: id ?? this.id,
    draftKey: draftKey ?? this.draftKey,
    name: name ?? this.name,
    capacity: capacity ?? this.capacity,
    bathroomAccess: bathroomAccess ?? this.bathroomAccess,
    description: description ?? this.description,
    beds: beds ?? this.beds,
    mediaIds: mediaIds ?? this.mediaIds,
  );
  @override
  List<Object?> get props => [
    id,
    draftKey,
    name,
    capacity,
    bathroomAccess,
    description,
    beds,
    mediaIds,
    draftDetails,
  ];
}
