import '../enums/owner_property_status.dart';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';

class OwnerPropertyContent extends Equatable {
  const OwnerPropertyContent({
    required this.id,
    required this.title,
    required this.mainImage,
    required this.location,
    required this.monthlyPrice,
    this.pricePeriod = '',
    required this.views,
    required this.visitRequests,
    required this.bedrooms,
    required this.area,
    required this.description,
    required this.photoCount,
    required this.status,
    this.rejectionReason = '',
  });

  factory OwnerPropertyContent.initial() {
    return const OwnerPropertyContent(
      id: '',
      title: '',
      mainImage: '',
      location: '',
      monthlyPrice: 0,
      pricePeriod: '',
      views: 0,
      visitRequests: 0,
      bedrooms: 0,
      area: 0,
      description: '',
      photoCount: 0,
      status: OwnerPropertyStatus.pending,
    );
  }

  factory OwnerPropertyContent.fromJson(Map<String, dynamic> json) {
    return OwnerPropertyContent(
      id: json['id'] ?? '',
      rejectionReason: json['rejection_reason']?.toString() ?? '',
      title: json['title'] ?? '',
      mainImage: json['main_image'] ?? '',
      location: json['location'] ?? '',
      monthlyPrice:
          EgyptianPound.parseAmount(json['price'] ?? json['monthly_price']) ??
          0,
      pricePeriod: json['price_period']?.toString() ?? '',
      views:
          (json['views_count'] as num?)?.toInt() ??
          (json['views'] as num?)?.toInt() ??
          0,
      visitRequests:
          (json['visits_count'] as num?)?.toInt() ??
          (json['visit_requests'] as num?)?.toInt() ??
          0,
      bedrooms: (json['bedrooms'] as num?)?.toInt() ?? 0,
      area: (json['area'] as num?)?.toInt() ?? 0,
      description: json['description'] ?? '',
      photoCount: json['photo_count'] ?? 0,
      status: OwnerPropertyStatusX.fromName(json['status']),
    );
  }

  final String id;
  final String rejectionReason;
  final String title;
  final String mainImage;
  final String location;
  final num monthlyPrice;
  final String pricePeriod;

  final int views;
  final int visitRequests;
  final int bedrooms;
  final int area;
  final String description;
  final int photoCount;
  final OwnerPropertyStatus status;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      if (rejectionReason.isNotEmpty) 'rejection_reason': rejectionReason,
      'title': title,
      'main_image': mainImage,
      'location': location,
      'monthly_price': monthlyPrice,
      'price_period': pricePeriod,
      'views': views,
      'visit_requests': visitRequests,
      'bedrooms': bedrooms,
      'area': area,
      'description': description,
      'photo_count': photoCount,
      'status': status.name,
    };
  }

  OwnerPropertyContent copyWith({
    String? id,
    String? rejectionReason,
    String? title,
    String? mainImage,
    String? location,
    num? monthlyPrice,
    String? pricePeriod,
    int? views,
    int? visitRequests,
    int? bedrooms,
    int? area,
    String? description,
    int? photoCount,
    OwnerPropertyStatus? status,
  }) {
    return OwnerPropertyContent(
      id: id ?? this.id,
      rejectionReason: rejectionReason ?? this.rejectionReason,
      title: title ?? this.title,
      mainImage: mainImage ?? this.mainImage,
      location: location ?? this.location,
      monthlyPrice: monthlyPrice ?? this.monthlyPrice,
      pricePeriod: pricePeriod ?? this.pricePeriod,
      views: views ?? this.views,
      visitRequests: visitRequests ?? this.visitRequests,
      bedrooms: bedrooms ?? this.bedrooms,
      area: area ?? this.area,
      description: description ?? this.description,
      photoCount: photoCount ?? this.photoCount,
      status: status ?? this.status,
    );
  }

  @override
  List<Object?> get props => [
    id,
    rejectionReason,
    title,
    mainImage,
    location,
    monthlyPrice,
    pricePeriod,
    views,
    visitRequests,
    bedrooms,
    area,
    description,
    photoCount,
    status,
  ];
}
