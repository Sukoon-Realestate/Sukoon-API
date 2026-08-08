import 'package:equatable/equatable.dart';
import 'package:melos_core/core/extensions/string_extension.dart';

class PropertyImageModel extends Equatable {
  final String id;
  final String image;
  final String name;
  final String description;
  final String createdAt;
  final String updatedAt;

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

  factory PropertyImageModel.fromJson(Map<String, dynamic> json) =>
      PropertyImageModel(
        id: json['id'] ?? '',
        image: json['image'] ?? '',
        name: json['name'] ?? '',
        description: json['description'] ?? '',
        createdAt: json['created_at'] ?? '',
        updatedAt: json['updated_at'] ?? '',
      );

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
  }) => PropertyImageModel(
    id: id ?? this.id,
    image: image ?? this.image,
    name: name ?? this.name,
    description: description ?? this.description,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );

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

class PropertyDetailsModel extends Equatable {
  final String id;
  final String owner;
  final String mainImage;
  final String title;
  final String description;
  final String price;
  final String pricePeriod;
  final String propertyType;
  final bool isFurnished;
  final bool isVerified;
  final int bedrooms;
  final int bathrooms;
  final int area;
  final String space;
  final int floor;
  final int rentalPeriod;
  final String suitableFor;
  final bool smokingAllowed;
  final String country;
  final String city;
  final String district;
  final String latitude;
  final String longitude;
  final bool hasWifi;
  final bool hasElevator;
  final bool hasGarage;
  final bool hasSecurity;
  final bool hasBalcony;
  final bool hasAirConditioning;
  final bool nearMetro;
  final bool hasNaturalGas;
  final bool hasElectricityMeter;
  final bool hasWaterMeter;
  final List<PropertyImageModel> images;
  final String createdAt;
  final String updatedAt;

  const PropertyDetailsModel({
    required this.id,
    required this.owner,
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
    required this.latitude,
    required this.longitude,
    required this.hasWifi,
    required this.hasElevator,
    required this.hasGarage,
    required this.hasSecurity,
    required this.hasBalcony,
    required this.hasAirConditioning,
    required this.nearMetro,
    required this.hasNaturalGas,
    required this.hasElectricityMeter,
    required this.hasWaterMeter,
    required this.images,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PropertyDetailsModel.initial() => const PropertyDetailsModel(
    id: '',
    owner: '',
    mainImage: '',
    title: '',
    description: '',
    price: '',
    pricePeriod: '',
    propertyType: '',
    isFurnished: false,
    isVerified: false,
    bedrooms: 0,
    bathrooms: 0,
    area: 0,
    space: '',
    floor: 0,
    rentalPeriod: 0,
    suitableFor: '',
    smokingAllowed: false,
    country: '',
    city: '',
    district: '',
    latitude: '',
    longitude: '',
    hasWifi: false,
    hasElevator: false,
    hasGarage: false,
    hasSecurity: false,
    hasBalcony: false,
    hasAirConditioning: false,
    nearMetro: false,
    hasNaturalGas: false,
    hasElectricityMeter: false,
    hasWaterMeter: false,
    images: [],
    createdAt: '',
    updatedAt: '',
  );

  factory PropertyDetailsModel.fromJson(Map<String, dynamic> json) =>
      PropertyDetailsModel(
        id: json['id'] ?? '',
        owner: json['owner'] ?? '',
        mainImage: json['main_image'] ?? '',
        title: json['title'] ?? '',
        description: json['description'] ?? '',
        price: json['price'] ?? '',
        pricePeriod: json['price_period'] ?? '',
        propertyType: json['property_type'] ?? '',
        isFurnished: json['is_furnished'] ?? false,
        isVerified: json['is_verified'] ?? false,
        bedrooms: (json['bedrooms'] as num?)?.toInt() ?? 0,
        bathrooms: (json['bathrooms'] as num?)?.toInt() ?? 0,
        area: (json['area'] as num?)?.toInt() ?? 0,
        space: json['space'] ?? '',
        floor: (json['floor'] as num?)?.toInt() ?? 0,
        rentalPeriod: (json['rental_period'] as num?)?.toInt() ?? 0,
        suitableFor: json['suitable_for'] ?? '',
        smokingAllowed: json['smoking_allowed'] ?? false,
        country: json['country'] ?? '',
        city: json['city'] ?? '',
        district: json['district'] ?? '',
        latitude: json['latitude'] ?? '',
        longitude: json['longitude'] ?? '',
        hasWifi: json['has_wifi'] ?? false,
        hasElevator: json['has_elevator'] ?? false,
        hasGarage: json['has_garage'] ?? false,
        hasSecurity: json['has_security'] ?? false,
        hasBalcony: json['has_balcony'] ?? false,
        hasAirConditioning: json['has_air_conditioning'] ?? false,
        nearMetro: json['near_metro'] ?? false,
        hasNaturalGas: json['has_natural_gas'] ?? false,
        hasElectricityMeter: json['has_electricity_meter'] ?? false,
        hasWaterMeter: json['has_water_meter'] ?? false,
        images:
            (json['images'] as List?)
                ?.map((e) => PropertyImageModel.fromJson(e))
                .toList() ??
            [],
        createdAt: json['created_at'] ?? '',
        updatedAt: json['updated_at'] ?? '',
      );

  Map<String, dynamic> toJson() => {
    'id': id,
    'owner': owner,
    'main_image': mainImage,
    'title': title,
    'description': description,
    'price': price,
    'price_period': pricePeriod,
    'property_type': propertyType,
    'is_furnished': isFurnished,
    'is_verified': isVerified,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'area': area,
    'space': space,
    'floor': floor,
    'rental_period': rentalPeriod,
    'suitable_for': suitableFor,
    'smoking_allowed': smokingAllowed,
    'country': country,
    'city': city,
    'district': district,
    'latitude': latitude,
    'longitude': longitude,
    'has_wifi': hasWifi,
    'has_elevator': hasElevator,
    'has_garage': hasGarage,
    'has_security': hasSecurity,
    'has_balcony': hasBalcony,
    'has_air_conditioning': hasAirConditioning,
    'near_metro': nearMetro,
    'has_natural_gas': hasNaturalGas,
    'has_electricity_meter': hasElectricityMeter,
    'has_water_meter': hasWaterMeter,
    'images': images.map((e) => e.toJson()).toList(),
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  PropertyDetailsModel copyWith({
    String? id,
    String? owner,
    String? mainImage,
    String? title,
    String? description,
    String? price,
    String? pricePeriod,
    String? propertyType,
    bool? isFurnished,
    bool? isVerified,
    int? bedrooms,
    int? bathrooms,
    int? area,
    String? space,
    int? floor,
    int? rentalPeriod,
    String? suitableFor,
    bool? smokingAllowed,
    String? country,
    String? city,
    String? district,
    String? latitude,
    String? longitude,
    bool? hasWifi,
    bool? hasElevator,
    bool? hasGarage,
    bool? hasSecurity,
    bool? hasBalcony,
    bool? hasAirConditioning,
    bool? nearMetro,
    bool? hasNaturalGas,
    bool? hasElectricityMeter,
    bool? hasWaterMeter,
    List<PropertyImageModel>? images,
    String? createdAt,
    String? updatedAt,
  }) => PropertyDetailsModel(
    id: id ?? this.id,
    owner: owner ?? this.owner,
    mainImage: mainImage ?? this.mainImage,
    title: title ?? this.title,
    description: description ?? this.description,
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    propertyType: propertyType ?? this.propertyType,
    isFurnished: isFurnished ?? this.isFurnished,
    isVerified: isVerified ?? this.isVerified,
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
    latitude: latitude ?? this.latitude,
    longitude: longitude ?? this.longitude,
    hasWifi: hasWifi ?? this.hasWifi,
    hasElevator: hasElevator ?? this.hasElevator,
    hasGarage: hasGarage ?? this.hasGarage,
    hasSecurity: hasSecurity ?? this.hasSecurity,
    hasBalcony: hasBalcony ?? this.hasBalcony,
    hasAirConditioning: hasAirConditioning ?? this.hasAirConditioning,
    nearMetro: nearMetro ?? this.nearMetro,
    hasNaturalGas: hasNaturalGas ?? this.hasNaturalGas,
    hasElectricityMeter: hasElectricityMeter ?? this.hasElectricityMeter,
    hasWaterMeter: hasWaterMeter ?? this.hasWaterMeter,
    images: images ?? this.images,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );

  String get formattedPrice => (double.tryParse(price) ?? 0).toCurrency();

  String get pricePeriodLabel {
    switch (pricePeriod) {
      case 'daily':
        return 'ج/يوم';
      case 'weekly':
        return 'ج/أسبوع';
      case 'yearly':
        return 'ج/سنة';
      case 'monthly':
      default:
        return 'ج/شهر';
    }
  }

  String get propertyTypeLabel {
    switch (propertyType) {
      case 'apartment':
        return 'شقة';
      case 'room':
        return 'غرفة';
      case 'duplex':
        return 'دوبلكس';
      case 'villa':
        return 'فيلا';
      case 'roof':
        return 'روف';
      case 'studio':
      default:
        return 'ستوديو';
    }
  }

  String get locationLabel => 'منطقة تقريبية · $district، $city';

  /// All displayable images — main image first, then the gallery images.
  List<String> get imageUrls => [
    if (mainImage.isNotEmpty) mainImage,
    ...images.map((e) => e.image).where((url) => url.isNotEmpty),
  ];

  /// Labels aligned with [imageUrls] (main image first).
  List<String> get photoLabels => [
    'الصورة الرئيسية',
    ...images.map((e) => e.name),
  ];

  List<String> get amenities => [
    if (hasWifi) 'واي فاي',
    if (hasElevator) 'أسانسير',
    if (hasGarage) 'جراج',
    if (hasSecurity) 'أمن',
    if (hasBalcony) 'بلكونة',
    if (hasAirConditioning) 'تكييف',
    if (isFurnished) 'مفروش',
    if (nearMetro) 'قريب من المترو',
    if (hasNaturalGas) 'غاز طبيعي',
    if (hasElectricityMeter) 'عداد كهرباء',
    if (hasWaterMeter) 'عداد مياه',
  ];

  @override
  List<Object?> get props => [
    id,
    owner,
    mainImage,
    title,
    description,
    price,
    pricePeriod,
    propertyType,
    isFurnished,
    isVerified,
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
    latitude,
    longitude,
    hasWifi,
    hasElevator,
    hasGarage,
    hasSecurity,
    hasBalcony,
    hasAirConditioning,
    nearMetro,
    hasNaturalGas,
    hasElectricityMeter,
    hasWaterMeter,
    images,
    createdAt,
    updatedAt,
  ];
}
