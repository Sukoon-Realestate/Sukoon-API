import 'package:equatable/equatable.dart';

class FavoritePropertyContent extends Equatable {
  const FavoritePropertyContent({
    required this.id,
    required this.mainImage,
    required this.title,
    required this.propertyType,
    required this.isFurnished,
    required this.bedrooms,
    required this.bathrooms,
    required this.area,
    required this.price,
    required this.pricePeriod,
    required this.rating,
    required this.savedAt,
    required this.isSaved,
    this.city = '',
    this.district = '',
    this.suitableFor = '',
    this.isVerified,
    this.smokingAllowed,
    this.amenities = const {},
  });

  const FavoritePropertyContent.initial()
    : id = '',
      mainImage = '',
      title = '',
      propertyType = '',
      isFurnished = false,
      bedrooms = 0,
      bathrooms = 0,
      area = 0,
      price = '',
      pricePeriod = '',
      rating = 0,
      savedAt = '',
      isSaved = false,
      city = '',
      district = '',
      suitableFor = '',
      isVerified = null,
      smokingAllowed = null,
      amenities = const {};

  factory FavoritePropertyContent.fromJson(Map<String, dynamic> json) {
    return FavoritePropertyContent(
      id: json['id']?.toString() ?? '',
      mainImage: json['main_image'] as String? ?? '',
      title: json['title'] as String? ?? '',
      propertyType: json['property_type'] as String? ?? '',
      isFurnished: _boolFromJson(json['is_furnished']) ?? false,
      bedrooms: (json['bedrooms'] as num?)?.toInt() ?? 0,
      bathrooms: (json['bathrooms'] as num?)?.toInt() ?? 0,
      area: (json['area'] as num?)?.toDouble() ?? 0,
      price: json['price']?.toString() ?? '',
      pricePeriod: json['price_period'] as String? ?? '',
      rating: (json['rating'] as num?)?.toDouble() ?? 0,
      savedAt: json['saved_at'] as String? ?? '',
      isSaved: _boolFromJson(json['is_saved']) ?? false,
      city:
          _locationValue(json['city']) ??
          (json['location'] is Map
              ? _locationValue((json['location'] as Map)['city']) ?? ''
              : ''),
      district:
          json['district']?.toString() ??
          (json['location'] is Map
              ? (json['location'] as Map)['district']?.toString() ?? ''
              : ''),
      suitableFor: json['suitable_for']?.toString() ?? '',
      isVerified: _boolFromJson(json['is_verified']),
      smokingAllowed: _boolFromJson(json['smoking_allowed']),
      amenities: _amenitiesFromJson(json['amenities']),
    );
  }

  final String id;
  final String mainImage;
  final String title;
  final String propertyType;
  final bool isFurnished;
  final int bedrooms;
  final int bathrooms;
  final double area;
  final String price;
  final String pricePeriod;
  final double rating;
  final String savedAt;
  final bool isSaved;
  final String city;
  final String district;
  final String suitableFor;
  final bool? isVerified;
  final bool? smokingAllowed;
  final Set<String> amenities;

  String get areaLabel => area == area.truncateToDouble()
      ? '${area.toInt()}م²'
      : '${area.toStringAsFixed(1)}م²';

  String get ratingLabel => rating == rating.truncateToDouble()
      ? rating.toInt().toString()
      : rating.toStringAsFixed(1);

  Map<String, dynamic> toJson() => {
    'id': id,
    'main_image': mainImage,
    'title': title,
    'property_type': propertyType,
    'is_furnished': isFurnished,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'area': area,
    'price': price,
    'price_period': pricePeriod,
    'rating': rating,
    'saved_at': savedAt,
    'is_saved': isSaved,
    if (city.isNotEmpty) 'city': city,
    if (district.isNotEmpty) 'district': district,
    if (suitableFor.isNotEmpty) 'suitable_for': suitableFor,
    if (isVerified != null) 'is_verified': isVerified,
    if (smokingAllowed != null) 'smoking_allowed': smokingAllowed,
    if (amenities.isNotEmpty)
      'amenities': amenities.toList(growable: false)..sort(),
  };

  FavoritePropertyContent copyWith({
    String? id,
    String? mainImage,
    String? title,
    String? propertyType,
    bool? isFurnished,
    int? bedrooms,
    int? bathrooms,
    double? area,
    String? price,
    String? pricePeriod,
    double? rating,
    String? savedAt,
    bool? isSaved,
    String? city,
    String? district,
    String? suitableFor,
    bool? isVerified,
    bool? smokingAllowed,
    Set<String>? amenities,
  }) {
    return FavoritePropertyContent(
      id: id ?? this.id,
      mainImage: mainImage ?? this.mainImage,
      title: title ?? this.title,
      propertyType: propertyType ?? this.propertyType,
      isFurnished: isFurnished ?? this.isFurnished,
      bedrooms: bedrooms ?? this.bedrooms,
      bathrooms: bathrooms ?? this.bathrooms,
      area: area ?? this.area,
      price: price ?? this.price,
      pricePeriod: pricePeriod ?? this.pricePeriod,
      rating: rating ?? this.rating,
      savedAt: savedAt ?? this.savedAt,
      isSaved: isSaved ?? this.isSaved,
      city: city ?? this.city,
      district: district ?? this.district,
      suitableFor: suitableFor ?? this.suitableFor,
      isVerified: isVerified ?? this.isVerified,
      smokingAllowed: smokingAllowed ?? this.smokingAllowed,
      amenities: amenities ?? this.amenities,
    );
  }

  @override
  List<Object?> get props => [
    id,
    mainImage,
    title,
    propertyType,
    isFurnished,
    bedrooms,
    bathrooms,
    area,
    price,
    pricePeriod,
    rating,
    savedAt,
    isSaved,
    city,
    district,
    suitableFor,
    isVerified,
    smokingAllowed,
    amenities,
  ];

  static Set<String> _amenitiesFromJson(dynamic value) {
    if (value is List) {
      return value
          .map((item) {
            if (item is Map) {
              return item['query_parameter'] ??
                  item['slug'] ??
                  item['value'] ??
                  item['name'] ??
                  item['id'];
            }
            return item;
          })
          .where((item) => item != null)
          .map((item) => item.toString())
          .toSet();
    }
    if (value is Map) {
      return value.entries
          .where((entry) => _boolFromJson(entry.value) == true)
          .map((entry) => entry.key.toString())
          .toSet();
    }
    return const {};
  }

  static String? _locationValue(dynamic value) {
    if (value == null) return null;
    if (value is Map) {
      final dynamic location = value['slug'] ?? value['name'] ?? value['id'];
      return location?.toString();
    }
    return value.toString();
  }

  static bool? _boolFromJson(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value == 1;
    if (value is String) {
      switch (value.trim().toLowerCase()) {
        case 'true':
        case '1':
        case 'yes':
          return true;
        case 'false':
        case '0':
        case 'no':
          return false;
      }
    }
    return null;
  }
}
