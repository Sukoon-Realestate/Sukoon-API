import 'package:equatable/equatable.dart';

class AvailablePlacesModel extends Equatable {
  const AvailablePlacesModel({required this.places});

  const AvailablePlacesModel.initial()
    : places = const [
        AvailablePlaceModel.initial(),
        AvailablePlaceModel.initial(),
        AvailablePlaceModel.initial(),
      ];

  factory AvailablePlacesModel.fromJson(Map<String, dynamic> json) {
    return AvailablePlacesModel(
      places:
          (json['places'] as List?)
              ?.whereType<Map>()
              .map(
                (place) => AvailablePlaceModel.fromJson(
                  Map<String, dynamic>.from(place),
                ),
              )
              .toList(growable: false) ??
          const [],
    );
  }

  final List<AvailablePlaceModel> places;

  Map<String, dynamic> toJson() => {
    'places': places.map((place) => place.toJson()).toList(growable: false),
  };

  AvailablePlacesModel copyWith({List<AvailablePlaceModel>? places}) {
    return AvailablePlacesModel(places: places ?? this.places);
  }

  @override
  List<Object?> get props => [places];
}

class AvailablePlaceModel extends Equatable {
  const AvailablePlaceModel({
    required this.country,
    required this.city,
    required this.district,
  });

  const AvailablePlaceModel.initial() : country = '', city = '', district = '';

  factory AvailablePlaceModel.fromJson(Map<String, dynamic> json) {
    return AvailablePlaceModel(
      country: json['country'] as String? ?? '',
      city: json['city'] as String? ?? '',
      district: json['district'] as String? ?? '',
    );
  }

  final String country;
  final String city;
  final String district;

  String get searchQuery => [
    district,
    city,
    country,
  ].where((value) => value.trim().isNotEmpty).join('، ');

  Map<String, dynamic> toJson() => {
    'country': country,
    'city': city,
    'district': district,
  };

  AvailablePlaceModel copyWith({
    String? country,
    String? city,
    String? district,
  }) {
    return AvailablePlaceModel(
      country: country ?? this.country,
      city: city ?? this.city,
      district: district ?? this.district,
    );
  }

  @override
  List<Object?> get props => [country, city, district];
}
