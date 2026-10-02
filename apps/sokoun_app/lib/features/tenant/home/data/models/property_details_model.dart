import 'package:equatable/equatable.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/string_extension.dart';

class PropertyImageModel extends Equatable {
  const PropertyImageModel({
    required this.id,
    required this.image,
    required this.name,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PropertyImageModel.initial() => const PropertyImageModel(
    id: '',
    image: '',
    name: '',
    description: '',
    createdAt: '',
    updatedAt: '',
  );

  factory PropertyImageModel.fromJson(Map<String, dynamic> json) {
    return PropertyImageModel(
      id: json['id'] as String? ?? '',
      image: json['image'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

  final String id;
  final String image;
  final String name;
  final String description;
  final String createdAt;
  final String updatedAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'image': image,
    'name': name,
    'description': description,
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  PropertyImageModel copyWith({
    String? id,
    String? image,
    String? name,
    String? description,
    String? createdAt,
    String? updatedAt,
  }) {
    return PropertyImageModel(
      id: id ?? this.id,
      image: image ?? this.image,
      name: name ?? this.name,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    image,
    name,
    description,
    createdAt,
    updatedAt,
  ];
}

class CityModel extends Equatable {
  const CityModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.governorate,
    required this.governorateName,
    required this.createdAt,
    required this.updatedAt,
  });

  const CityModel.initial()
    : id = '',
      name = '',
      slug = '',
      governorate = '',
      governorateName = '',
      createdAt = '',
      updatedAt = '';

  factory CityModel.fromJson(Map<String, dynamic> json) {
    return CityModel(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      governorate: json['governorate'] as String? ?? '',
      governorateName: json['governorate_name'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

  final String id;
  final String name;
  final String slug;
  final String governorate;
  final String governorateName;
  final String createdAt;
  final String updatedAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'slug': slug,
    'governorate': governorate,
    'governorate_name': governorateName,
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  CityModel copyWith({
    String? id,
    String? name,
    String? slug,
    String? governorate,
    String? governorateName,
    String? createdAt,
    String? updatedAt,
  }) {
    return CityModel(
      id: id ?? this.id,
      name: name ?? this.name,
      slug: slug ?? this.slug,
      governorate: governorate ?? this.governorate,
      governorateName: governorateName ?? this.governorateName,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    slug,
    governorate,
    governorateName,
    createdAt,
    updatedAt,
  ];
}

class PropertyDetailsModel extends Equatable {
  const PropertyDetailsModel({
    this.video,
    this.videoDuration,
    this.propertyLink = '',
    this.isOwnerVerified = false,
    this.isOwnershipVerified = false,
    required this.id,
    required this.owner,
    required this.ownerId,
    required this.mainImage,
    required this.title,
    required this.description,
    required this.price,
    required this.pricePeriod,
    required this.propertyType,
    required this.isFurnished,
    required this.isVerified,
    required this.bedrooms,
    required this.bathrooms,
    required this.area,
    required this.space,
    required this.floor,
    required this.rentalPeriod,
    required this.suitableFor,
    required this.smokingAllowed,
    required this.country,
    required this.city,
    required this.district,
    required this.street,
    required this.buildingYear,
    required this.deposit,
    required this.ownershipProof,
    required this.latitude,
    required this.longitude,
    required this.amenities,
    required this.isFav,
    required this.isSaved,
    required this.rating,
    required this.images,
    required this.createdAt,
    required this.updatedAt,
  });

  const PropertyDetailsModel.initial()
    : video = null,
      videoDuration = null,
      propertyLink = '',
      isOwnerVerified = false,
      isOwnershipVerified = false,
      id = '',
      owner = '',
      ownerId = '',
      mainImage = '',
      title = '',
      description = '',
      price = '',
      pricePeriod = '',
      propertyType = '',
      isFurnished = false,
      isVerified = false,
      bedrooms = 0,
      bathrooms = 0,
      area = 0,
      space = '',
      floor = null,
      rentalPeriod = 0,
      suitableFor = '',
      smokingAllowed = null,
      country = '',
      city = const CityModel.initial(),
      district = '',
      street = '',
      buildingYear = 0,
      deposit = '',
      ownershipProof = '',
      latitude = '',
      longitude = '',
      amenities = const [],
      isFav = false,
      isSaved = false,
      rating = 0,
      images = const [],
      createdAt = '',
      updatedAt = '';

  factory PropertyDetailsModel.fromJson(Map<String, dynamic> json) {
    final Object? ownerValue = json['owner'];
    final Map<String, dynamic> ownerJson = ownerValue is Map
        ? Map<String, dynamic>.from(ownerValue)
        : const {};
    final String ownerString = ownerValue is String ? ownerValue.trim() : '';
    final bool ownerStringIsId = RegExp(
      r'^[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}$',
    ).hasMatch(ownerString);
    final String ownerName =
        ownerJson['full_name']?.toString() ??
        ownerJson['name']?.toString() ??
        json['owner_name']?.toString() ??
        (ownerStringIsId ? '' : ownerString);
    return PropertyDetailsModel(
      video: json['video'] as String?,
      videoDuration: (json['video_duration'] as num?)?.toInt(),
      propertyLink: json['property_link'] as String? ?? '',
      id: json['id'] as String? ?? '',
      owner: ownerName,
      ownerId:
          ownerJson['id']?.toString() ??
          json['owner_id']?.toString() ??
          (ownerStringIsId ? ownerString : ''),
      mainImage: json['main_image'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      price: json['price']?.toString() ?? '',
      pricePeriod: json['price_period'] as String? ?? '',
      propertyType: json['property_type'] as String? ?? '',
      isFurnished: json['is_furnished'] as bool? ?? false,
      isVerified: json['is_verified'] as bool? ?? false,
      isOwnerVerified:
          (ownerJson['is_verified'] as bool?) ??
          (json['owner_is_verified'] == true),
      isOwnershipVerified: json['is_ownership_verified'] == true,
      bedrooms: (json['bedrooms'] as num?)?.toInt() ?? 0,
      bathrooms: (json['bathrooms'] as num?)?.toInt() ?? 0,
      area: (json['area'] as num?)?.toInt() ?? 0,
      space: json['space']?.toString() ?? '',
      floor: int.tryParse(json['floor']?.toString() ?? ''),
      rentalPeriod: (json['rental_period'] as num?)?.toInt() ?? 0,
      suitableFor: json['suitable_for'] as String? ?? '',
      smokingAllowed: json['smoking_allowed'] as bool?,
      country: json['country'] as String? ?? '',
      city: json['city'] is Map
          ? CityModel.fromJson(Map<String, dynamic>.from(json['city'] as Map))
          : const CityModel.initial(),
      district: json['district'] as String? ?? '',
      street: json['street'] as String? ?? '',
      buildingYear: int.tryParse('${json['building_year'] ?? ''}') ?? 0,
      deposit: json['deposit']?.toString() ?? '',
      ownershipProof: _propertyFileUrl(json['ownership_proof']),
      latitude: json['latitude']?.toString() ?? '',
      longitude: json['longitude']?.toString() ?? '',
      amenities:
          (json['amenities'] as List?)?.whereType<String>().toList(
            growable: false,
          ) ??
          const [],
      isFav: json['is_fav'] as bool? ?? false,
      isSaved: json['is_saved'] as bool? ?? false,
      rating: (json['rating'] as num?)?.toDouble() ?? 0,
      images:
          (json['images'] as List?)
              ?.whereType<Map>()
              .map(
                (image) => PropertyImageModel.fromJson(
                  Map<String, dynamic>.from(image),
                ),
              )
              .toList(growable: false) ??
          const [],
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

  final String id;
  final String owner;
  final String ownerId;
  final String? video;
  final int? videoDuration;
  final String propertyLink;
  final String mainImage;
  final String title;
  final String description;
  final String price;
  final String pricePeriod;
  final String propertyType;
  final bool isFurnished;
  final bool isVerified;
  final bool isOwnerVerified;
  final bool isOwnershipVerified;
  final int bedrooms;
  final int bathrooms;
  final int area;
  final String space;
  final int? floor;
  final int rentalPeriod;
  final String suitableFor;
  final bool? smokingAllowed;
  final String country;
  final CityModel city;
  final String district;
  final String street;
  final int buildingYear;
  final String deposit;
  final String ownershipProof;
  final String latitude;
  final String longitude;
  final List<String> amenities;
  final bool isFav;
  final bool isSaved;
  final double rating;
  final List<PropertyImageModel> images;
  final String createdAt;
  final String updatedAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'owner': owner,
    'owner_id': ownerId,
    'video': video,
    'video_duration': videoDuration,
    'property_link': propertyLink,
    'main_image': mainImage,
    'title': title,
    'description': description,
    'price': price,
    'price_period': pricePeriod,
    'property_type': propertyType,
    'is_furnished': isFurnished,
    'is_verified': isVerified,
    'owner_is_verified': isOwnerVerified,
    'is_ownership_verified': isOwnershipVerified,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'area': area,
    'space': space,
    'floor': floor,
    'rental_period': rentalPeriod,
    'suitable_for': suitableFor,
    'smoking_allowed': smokingAllowed,
    'country': country,
    'city': city.toJson(),
    'district': district,
    'street': street,
    'building_year': buildingYear,
    'deposit': deposit,
    'ownership_proof': ownershipProof,
    'latitude': latitude,
    'longitude': longitude,
    'amenities': amenities,
    'is_fav': isFav,
    'is_saved': isSaved,
    'rating': rating,
    'images': images.map((image) => image.toJson()).toList(growable: false),
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  PropertyDetailsModel copyWith({
    String? video,
    int? videoDuration,
    String? propertyLink,
    String? id,
    String? owner,
    String? ownerId,
    String? mainImage,
    String? title,
    String? description,
    String? price,
    String? pricePeriod,
    String? propertyType,
    bool? isFurnished,
    bool? isVerified,
    bool? isOwnerVerified,
    bool? isOwnershipVerified,
    int? bedrooms,
    int? bathrooms,
    int? area,
    String? space,
    int? floor,
    int? rentalPeriod,
    String? suitableFor,
    bool? smokingAllowed,
    String? country,
    CityModel? city,
    String? district,
    String? street,
    int? buildingYear,
    String? deposit,
    String? ownershipProof,
    String? latitude,
    String? longitude,
    List<String>? amenities,
    bool? isFav,
    bool? isSaved,
    double? rating,
    List<PropertyImageModel>? images,
    String? createdAt,
    String? updatedAt,
  }) {
    return PropertyDetailsModel(
      video: video ?? this.video,
      videoDuration: videoDuration ?? this.videoDuration,
      propertyLink: propertyLink ?? this.propertyLink,
      id: id ?? this.id,
      owner: owner ?? this.owner,
      ownerId: ownerId ?? this.ownerId,
      mainImage: mainImage ?? this.mainImage,
      title: title ?? this.title,
      description: description ?? this.description,
      price: price ?? this.price,
      pricePeriod: pricePeriod ?? this.pricePeriod,
      propertyType: propertyType ?? this.propertyType,
      isFurnished: isFurnished ?? this.isFurnished,
      isVerified: isVerified ?? this.isVerified,
      isOwnerVerified: isOwnerVerified ?? this.isOwnerVerified,
      isOwnershipVerified: isOwnershipVerified ?? this.isOwnershipVerified,
      bedrooms: bedrooms ?? this.bedrooms,
      bathrooms: bathrooms ?? this.bathrooms,
      area: area ?? this.area,
      space: space ?? this.space,
      floor: floor ?? this.floor,
      rentalPeriod: rentalPeriod ?? this.rentalPeriod,
      suitableFor: suitableFor ?? this.suitableFor,
      smokingAllowed: smokingAllowed ?? this.smokingAllowed,
      country: country ?? this.country,
      city: city ?? this.city,
      district: district ?? this.district,
      street: street ?? this.street,
      buildingYear: buildingYear ?? this.buildingYear,
      deposit: deposit ?? this.deposit,
      ownershipProof: ownershipProof ?? this.ownershipProof,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      amenities: amenities ?? this.amenities,
      isFav: isFav ?? this.isFav,
      isSaved: isSaved ?? this.isSaved,
      rating: rating ?? this.rating,
      images: images ?? this.images,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  String get formattedPrice => (double.tryParse(price) ?? 0).toCurrency();

  String get pricePeriodLabel {
    switch (pricePeriod) {
      case 'daily':
        return LocaleKeys.tenantPropertyDetailsDailyPriceUnit;
      case 'weekly':
        return LocaleKeys.tenantPropertyDetailsWeeklyPriceUnit;
      case 'yearly':
        return LocaleKeys.tenantPropertyDetailsYearlyPriceUnit;
      case 'monthly':
        return LocaleKeys.tenantPropertyDetailsMonthlyPriceUnit;
      default:
        return pricePeriod;
    }
  }

  String get propertyTypeLabel => propertyTypeLabelFor(propertyType);

  static String propertyTypeLabelFor(String value) {
    switch (value) {
      case 'apartment':
        return LocaleKeys.ownerAddPropertyApartment;
      case 'room':
        return LocaleKeys.ownerAddPropertyRoom;
      case 'duplex':
        return LocaleKeys.tenantPropertyDetailsDuplex;
      case 'villa':
        return LocaleKeys.ownerAddPropertyVilla;
      case 'floor':
        return LocaleKeys.ownerAddPropertyWholeFloor;
      case 'roof':
        return LocaleKeys.ownerAddPropertyRoof;
      case 'studio':
        return LocaleKeys.ownerAddPropertyStudio;
      default:
        return value;
    }
  }

  String get locationLabel => LocaleKeys
      .tenantPropertyDetailsApproximateLocation
      .replaceAll('{district}', district)
      .replaceAll('{city}', city.name);

  /// One ordered source for gallery URLs, names, and descriptions.
  List<PropertyImageModel> get galleryImages {
    final List<PropertyImageModel> photos = [];
    final Set<String> seen = {};
    if (mainImage.trim().isNotEmpty) {
      final PropertyImageModel main = images.firstWhere(
        (image) => image.image == mainImage,
        orElse: () => PropertyImageModel.initial().copyWith(image: mainImage),
      );
      photos.add(
        main.copyWith(
          name: main.name.trim().isEmpty
              ? LocaleKeys.tenantPropertyDetailsMainPhoto
              : main.name,
        ),
      );
      seen.add(mainImage);
    }
    for (final PropertyImageModel image in images) {
      if (image.image.trim().isNotEmpty && seen.add(image.image)) {
        photos.add(image);
      }
    }
    return photos;
  }

  List<String> get imageUrls =>
      galleryImages.map((image) => image.image).toList(growable: false);

  List<String> get photoLabels => galleryImages.indexed
      .map((entry) {
        final (int index, PropertyImageModel image) = entry;
        return image.name.trim().isNotEmpty
            ? image.name
            : '${LocaleKeys.tenantPropertyDetailsPhotoCountUnit} ${index + 1}';
      })
      .toList(growable: false);

  List<String> get amenityLabels => amenities
      .map(_amenityLabel)
      .where((label) => label.isNotEmpty)
      .toList(growable: false);

  String _amenityLabel(String amenity) {
    switch (amenity) {
      case 'wifi':
        return LocaleKeys.tenantFilterWifi;
      case 'elevator':
        return LocaleKeys.tenantFilterElevator;
      case 'garage':
        return LocaleKeys.tenantFilterGarage;
      case 'security':
        return LocaleKeys.tenantFilterSecurity;
      case 'balcony':
        return LocaleKeys.tenantFilterBalcony;
      case 'air_conditioning':
        return LocaleKeys.tenantFilterAirConditioning;
      case 'near_metro':
        return LocaleKeys.tenantFilterNearMetro;
      case 'natural_gas':
        return LocaleKeys.tenantFilterNaturalGas;
      case 'electricity_meter':
        return LocaleKeys.tenantFilterElectricityMeter;
      case 'water_meter':
        return LocaleKeys.tenantFilterWaterMeter;
      default:
        return amenity;
    }
  }

  @override
  List<Object?> get props => [
    id,
    owner,
    ownerId,
    video,
    videoDuration,
    propertyLink,
    mainImage,
    title,
    description,
    price,
    pricePeriod,
    propertyType,
    isFurnished,
    isVerified,
    isOwnerVerified,
    isOwnershipVerified,
    bedrooms,
    bathrooms,
    area,
    space,
    floor,
    rentalPeriod,
    suitableFor,
    smokingAllowed,
    country,
    city,
    district,
    street,
    buildingYear,
    deposit,
    ownershipProof,
    latitude,
    longitude,
    amenities,
    isFav,
    isSaved,
    rating,
    images,
    createdAt,
    updatedAt,
  ];
}

String _propertyFileUrl(dynamic value) {
  if (value is Map) {
    final Map<String, dynamic> file = Map<String, dynamic>.from(value);
    return (file['url'] ?? file['file'] ?? file['image'])?.toString() ?? '';
  }
  return value?.toString() ?? '';
}
