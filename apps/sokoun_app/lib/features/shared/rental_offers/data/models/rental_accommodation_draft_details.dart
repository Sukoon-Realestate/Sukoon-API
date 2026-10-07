import 'package:equatable/equatable.dart';
import '../rental_json.dart';

/// Device-draft fields awaiting an agreed backend contract. These are never
/// parsed from API responses or added to rental v1 request bodies.
class RentalRoomDraftDetails extends Equatable {
  const RentalRoomDraftDetails({
    this.area = '',
    this.furnished,
    this.contents = const [],
    this.features = const [],
    this.photoRefs = const [],
  });
  factory RentalRoomDraftDetails.fromJson(Map<String, dynamic> json) =>
      RentalRoomDraftDetails(
        area: json['area']?.toString() ?? '',
        furnished: json['furnished'] is bool ? json['furnished'] as bool : null,
        contents: rentalStrings(json['contents']),
        features: rentalStrings(json['features']),
        photoRefs: rentalStrings(json['photo_refs']),
      );
  final String area;
  final bool? furnished;
  final List<String> contents, features, photoRefs;
  num? get knownArea {
    final value = num.tryParse(area);
    return value != null && value.isFinite && value > 0 ? value : null;
  }

  bool get isValid => area.trim().isEmpty || knownArea != null;
  bool get hasData =>
      area.isNotEmpty ||
      furnished != null ||
      contents.isNotEmpty ||
      features.isNotEmpty ||
      photoRefs.isNotEmpty;
  Map<String, dynamic> toJson() => {
    'area': area,
    'furnished': furnished,
    'contents': contents,
    'features': features,
    'photo_refs': photoRefs,
  };
  RentalRoomDraftDetails copyWith({
    String? area,
    bool? furnished,
    bool clearFurnished = false,
    List<String>? contents,
    List<String>? features,
    List<String>? photoRefs,
  }) => RentalRoomDraftDetails(
    area: area ?? this.area,
    furnished: clearFurnished ? null : furnished ?? this.furnished,
    contents: contents ?? this.contents,
    features: features ?? this.features,
    photoRefs: photoRefs ?? this.photoRefs,
  );
  @override
  List<Object?> get props => [area, furnished, contents, features, photoRefs];
}

class RentalBedDraftDetails extends Equatable {
  const RentalBedDraftDetails({
    this.type = '',
    this.storage = '',
    this.description = '',
    this.photoRefs = const [],
  });
  factory RentalBedDraftDetails.fromJson(Map<String, dynamic> json) =>
      RentalBedDraftDetails(
        type: json['type']?.toString() ?? '',
        storage: json['storage']?.toString() ?? '',
        description: json['description']?.toString() ?? '',
        photoRefs: rentalStrings(json['photo_refs']),
      );
  final String type, storage, description;
  final List<String> photoRefs;
  bool get hasData =>
      type.isNotEmpty ||
      storage.isNotEmpty ||
      description.isNotEmpty ||
      photoRefs.isNotEmpty;
  Map<String, dynamic> toJson() => {
    'type': type,
    'storage': storage,
    'description': description,
    'photo_refs': photoRefs,
  };
  RentalBedDraftDetails copyWith({
    String? type,
    String? storage,
    String? description,
    List<String>? photoRefs,
  }) => RentalBedDraftDetails(
    type: type ?? this.type,
    storage: storage ?? this.storage,
    description: description ?? this.description,
    photoRefs: photoRefs ?? this.photoRefs,
  );
  @override
  List<Object?> get props => [type, storage, description, photoRefs];
}

class RentalSharedDraftDetails extends Equatable {
  const RentalSharedDraftDetails({
    this.facilities = const [],
    this.rules = const [],
    this.photoRefs = const [],
  });
  factory RentalSharedDraftDetails.fromJson(Map<String, dynamic> json) =>
      RentalSharedDraftDetails(
        facilities: rentalStrings(json['facilities']),
        rules: rentalStrings(json['rules']),
        photoRefs: rentalStrings(json['photo_refs']),
      );
  final List<String> facilities, rules, photoRefs;
  bool get hasData =>
      facilities.isNotEmpty || rules.isNotEmpty || photoRefs.isNotEmpty;
  Map<String, dynamic> toJson() => {
    'facilities': facilities,
    'rules': rules,
    'photo_refs': photoRefs,
  };
  RentalSharedDraftDetails copyWith({
    List<String>? facilities,
    List<String>? rules,
    List<String>? photoRefs,
  }) => RentalSharedDraftDetails(
    facilities: facilities ?? this.facilities,
    rules: rules ?? this.rules,
    photoRefs: photoRefs ?? this.photoRefs,
  );
  @override
  List<Object?> get props => [facilities, rules, photoRefs];
}

class RentalOfferDraftDetails extends Equatable {
  const RentalOfferDraftDetails({this.groupFacilities = const []});
  factory RentalOfferDraftDetails.fromJson(Map<String, dynamic> json) =>
      RentalOfferDraftDetails(
        groupFacilities: rentalStrings(json['group_facilities']),
      );
  final List<String> groupFacilities;
  bool get hasData => groupFacilities.isNotEmpty;
  Map<String, dynamic> toJson() => {'group_facilities': groupFacilities};
  RentalOfferDraftDetails copyWith({List<String>? groupFacilities}) =>
      RentalOfferDraftDetails(
        groupFacilities: groupFacilities ?? this.groupFacilities,
      );
  @override
  List<Object?> get props => [groupFacilities];
}
