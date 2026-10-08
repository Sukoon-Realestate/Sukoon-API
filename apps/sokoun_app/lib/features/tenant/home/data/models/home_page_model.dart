import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:equatable/equatable.dart';

class HomePageModel extends Equatable {
  final int count;
  final String? next;
  final String? previous;
  final List<HomePropertyModel> results;
  final HomeVisitBannerModel? banner;

  const HomePageModel({
    required this.count,
    this.next,
    this.previous,
    required this.results,
    this.banner,
  });

  const HomePageModel.initial()
    : count = 0,
      next = null,
      previous = null,
      results = const [],
      banner = null;

  factory HomePageModel.fromJson(Map<String, dynamic> json) => HomePageModel(
    count: json['count'] ?? 0,
    next: json['next'],
    previous: json['previous'],
    results:
        (json['results'] as List?)
            ?.map((e) => HomePropertyModel.fromJson(e))
            .toList() ??
        [],
    banner: json['banner'] is Map
        ? HomeVisitBannerModel.fromJson(
            Map<String, dynamic>.from(json['banner'] as Map),
          )
        : null,
  );

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map((e) => e.toJson()).toList(),
    'banner': banner?.toJson(),
  };

  HomePageModel copyWith({
    int? count,
    String? next,
    String? previous,
    List<HomePropertyModel>? results,
    HomeVisitBannerModel? banner,
  }) => HomePageModel(
    count: count ?? this.count,
    next: next ?? this.next,
    previous: previous ?? this.previous,
    results: results ?? this.results,
    banner: banner ?? this.banner,
  );

  @override
  List<Object?> get props => [count, next, previous, results, banner];
}

class HomeVisitBannerModel extends Equatable {
  const HomeVisitBannerModel({
    required this.visitId,
    required this.propertyId,
    required this.propertyTitle,
    required this.propertyDistrict,
    required this.visitDate,
    required this.visitTime,
    required this.isToday,
  });

  const HomeVisitBannerModel.initial()
    : visitId = '',
      propertyId = '',
      propertyTitle = '',
      propertyDistrict = '',
      visitDate = '',
      visitTime = '',
      isToday = false;

  factory HomeVisitBannerModel.fromJson(Map<String, dynamic> json) =>
      HomeVisitBannerModel(
        visitId: json['visit_id']?.toString() ?? '',
        propertyId: json['property_id']?.toString() ?? '',
        propertyTitle: json['property_title']?.toString() ?? '',
        propertyDistrict: json['property_district']?.toString() ?? '',
        visitDate: json['visit_date']?.toString() ?? '',
        visitTime: json['visit_time']?.toString() ?? '',
        isToday: json['is_today'] == true,
      );

  final String visitId;
  final String propertyId;
  final String propertyTitle;
  final String propertyDistrict;
  final String visitDate;
  final String visitTime;
  final bool isToday;

  bool get isEmpty =>
      propertyTitle.trim().isEmpty &&
      propertyDistrict.trim().isEmpty &&
      visitDate.trim().isEmpty &&
      visitTime.trim().isEmpty;

  Map<String, dynamic> toJson() => {
    'visit_id': visitId,
    'property_id': propertyId,
    'property_title': propertyTitle,
    'property_district': propertyDistrict,
    'visit_date': visitDate,
    'visit_time': visitTime,
    'is_today': isToday,
  };

  HomeVisitBannerModel copyWith({
    String? visitId,
    String? propertyId,
    String? propertyTitle,
    String? propertyDistrict,
    String? visitDate,
    String? visitTime,
    bool? isToday,
  }) => HomeVisitBannerModel(
    visitId: visitId ?? this.visitId,
    propertyId: propertyId ?? this.propertyId,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    propertyDistrict: propertyDistrict ?? this.propertyDistrict,
    visitDate: visitDate ?? this.visitDate,
    visitTime: visitTime ?? this.visitTime,
    isToday: isToday ?? this.isToday,
  );

  @override
  List<Object?> get props => [
    visitId,
    propertyId,
    propertyTitle,
    propertyDistrict,
    visitDate,
    visitTime,
    isToday,
  ];
}

class HomePropertyModel extends Equatable {
  final String id;
  final String mainImage;
  final int imagesCount;
  final String title;
  final String price;
  final String pricePeriod;
  final String propertyType;
  final int area;
  final double rate;
  final bool isSponsored;
  final RentalListingSummary? rentalSummary;
  final int? rentalSchemaVersion;
  final String location;
  bool get hasRentalOffers =>
      rentalSchemaVersion != null || rentalSummary != null;

  const HomePropertyModel({
    this.rentalSummary,
    this.rentalSchemaVersion,
    this.location = '',
    required this.id,
    required this.mainImage,
    required this.imagesCount,
    required this.title,
    required this.price,
    required this.pricePeriod,
    required this.propertyType,
    required this.area,
    required this.rate,
    this.isSponsored = false,
  });

  const HomePropertyModel.initial()
    : rentalSummary = null,
      rentalSchemaVersion = null,
      location = '',
      id = '',
      mainImage = '',
      imagesCount = 0,
      title = '',
      price = '',
      pricePeriod = '',
      propertyType = '',
      area = 0,
      rate = 0,
      isSponsored = false;

  factory HomePropertyModel.fromJson(Map<String, dynamic> json) =>
      HomePropertyModel(
        rentalSummary: RentalListingSummary.read(json),
        rentalSchemaVersion: int.tryParse(
          '${json['rental_schema_version'] ?? ''}',
        ),
        location: json['location_label']?.toString() ?? '',
        id: json['id'] ?? '',
        mainImage: json['main_image'] ?? '',
        imagesCount: (json['images_count'] as num?)?.toInt() ?? 0,
        title: json['title'] ?? '',
        price: json['price'] ?? '',
        pricePeriod: json['price_period'] ?? '',
        propertyType: json['property_type'] ?? '',
        area: (json['area'] as num?)?.toInt() ?? 0,
        rate: (json['rate'] as num?)?.toDouble() ?? 0,
        isSponsored: json['is_sponsored'] == true,
      );

  Map<String, dynamic> toJson() => {
    'id': id,
    if (rentalSummary != null) 'rental_summary': rentalSummary!.toJson(),
    if (rentalSchemaVersion != null)
      'rental_schema_version': rentalSchemaVersion,
    'location_label': location,
    'main_image': mainImage,
    'images_count': imagesCount,
    'title': title,
    'price': price,
    'price_period': pricePeriod,
    'property_type': propertyType,
    'area': area,
    'rate': rate,
    'is_sponsored': isSponsored,
  };

  HomePropertyModel copyWith({
    RentalListingSummary? rentalSummary,
    int? rentalSchemaVersion,
    String? location,
    String? id,
    String? mainImage,
    int? imagesCount,
    String? title,
    String? price,
    String? pricePeriod,
    String? propertyType,
    int? area,
    double? rate,
    bool? isSponsored,
  }) => HomePropertyModel(
    rentalSummary: rentalSummary ?? this.rentalSummary,
    rentalSchemaVersion: rentalSchemaVersion ?? this.rentalSchemaVersion,
    location: location ?? this.location,
    id: id ?? this.id,
    mainImage: mainImage ?? this.mainImage,
    imagesCount: imagesCount ?? this.imagesCount,
    title: title ?? this.title,
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    propertyType: propertyType ?? this.propertyType,
    area: area ?? this.area,
    rate: rate ?? this.rate,
    isSponsored: isSponsored ?? this.isSponsored,
  );

  @override
  List<Object?> get props => [
    rentalSummary,
    rentalSchemaVersion,
    location,
    id,
    mainImage,
    imagesCount,
    title,
    price,
    pricePeriod,
    propertyType,
    area,
    rate,
    isSponsored,
  ];
}
