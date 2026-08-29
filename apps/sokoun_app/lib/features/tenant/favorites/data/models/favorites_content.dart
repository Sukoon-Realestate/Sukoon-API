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
      isSaved = false;

  factory FavoritePropertyContent.fromJson(Map<String, dynamic> json) {
    return FavoritePropertyContent(
      id: json['id']?.toString() ?? '',
      mainImage: json['main_image'] as String? ?? '',
      title: json['title'] as String? ?? '',
      propertyType: json['property_type'] as String? ?? '',
      isFurnished: json['is_furnished'] as bool? ?? false,
      bedrooms: (json['bedrooms'] as num?)?.toInt() ?? 0,
      bathrooms: (json['bathrooms'] as num?)?.toInt() ?? 0,
      area: (json['area'] as num?)?.toDouble() ?? 0,
      price: json['price']?.toString() ?? '',
      pricePeriod: json['price_period'] as String? ?? '',
      rating: (json['rating'] as num?)?.toDouble() ?? 0,
      savedAt: json['saved_at'] as String? ?? '',
      isSaved: json['is_saved'] as bool? ?? false,
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
  ];
}

abstract final class FavoritesContent {
  static const List<FavoritePropertyContent> initialItems = [
    FavoritePropertyContent(
      id: '1',
      mainImage: '',
      title: 'شقة مفروشة — مدينة نصر',
      propertyType: 'apartment',
      isFurnished: true,
      bedrooms: 3,
      bathrooms: 2,
      area: 90,
      price: '6,500',
      pricePeriod: 'monthly',
      rating: 4.8,
      savedAt: '',
      isSaved: true,
    ),
    FavoritePropertyContent(
      id: '2',
      mainImage: '',
      title: 'ستوديو عصري — التجمع',
      propertyType: 'studio',
      isFurnished: true,
      bedrooms: 1,
      bathrooms: 1,
      area: 55,
      price: '4,200',
      pricePeriod: 'monthly',
      rating: 4.6,
      savedAt: '',
      isSaved: true,
    ),
    FavoritePropertyContent(
      id: '3',
      mainImage: '',
      title: 'شقة 3 غرف — المهندسين',
      propertyType: 'apartment',
      isFurnished: false,
      bedrooms: 3,
      bathrooms: 2,
      area: 120,
      price: '8,800',
      pricePeriod: 'monthly',
      rating: 4.9,
      savedAt: '',
      isSaved: true,
    ),
  ];
}
