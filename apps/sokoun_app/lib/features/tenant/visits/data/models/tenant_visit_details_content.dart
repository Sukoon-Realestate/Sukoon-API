import '../visit_json.dart';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/property_review.dart';
import 'tenant_visit_content.dart';

class TenantVisitDetailsContent extends Equatable {
  const TenantVisitDetailsContent({
    required this.visit,
    this.propertyId = '',
    this.location = '',
    this.price = '',
    this.pricePeriod = '',
    this.bedrooms,
    this.note = '',
    this.maskedPhone = '',
    this.ownerVerified = false,
    this.review,
  });
  const TenantVisitDetailsContent.initial()
    : visit = const TenantVisitContent.initial(),
      propertyId = '',
      location = '',
      price = '',
      pricePeriod = '',
      bedrooms = null,
      note = '',
      maskedPhone = '',
      ownerVerified = false,
      review = null;

  factory TenantVisitDetailsContent.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> property = visitJsonMap(json['property']);
    final Map<String, dynamic> owner = visitJsonMap(json['owner']);
    return TenantVisitDetailsContent(
      visit: TenantVisitContent.fromJson(json),
      propertyId: property['id']?.toString() ?? '',
      location: property['location']?.toString() ?? '',
      price: property['price']?.toString() ?? '',
      pricePeriod: property['price_period']?.toString() ?? '',
      bedrooms: int.tryParse(property['bedrooms']?.toString() ?? ''),
      note: json['note']?.toString() ?? '',
      maskedPhone: owner['masked_phone_number']?.toString() ?? '',
      ownerVerified: owner['is_verified'] ?? false,
      review: json['review'] is Map
          ? PropertyReview.fromJson(visitJsonMap(json['review']))
          : null,
    );
  }
  final TenantVisitContent visit;
  get rentalSelection => visit.rentalSelection;
  final String propertyId, location, price, pricePeriod, note, maskedPhone;
  final int? bedrooms;
  final bool ownerVerified;
  final PropertyReview? review;
  Map<String, dynamic> toJson() => {
    ...visit.toJson(),
    'property': {
      'id': propertyId,
      'title': visit.propertyTitle,
      'location': location,
      'price': price,
      'price_period': pricePeriod,
      'bedrooms': bedrooms,
    },
    'owner': {
      'id': visit.ownerId,
      'name': visit.ownerName,
      'phone_number': visit.ownerPhone,
      'is_phone_revealed': visit.isPhoneRevealed,
      'masked_phone_number': maskedPhone,
      'is_verified': ownerVerified,
    },
    'note': note,
    'review': review?.toJson(),
  };
  TenantVisitDetailsContent copyWith({
    TenantVisitContent? visit,
    String? propertyId,
    String? location,
    String? price,
    String? pricePeriod,
    int? bedrooms,
    String? note,
    String? maskedPhone,
    bool? ownerVerified,
    PropertyReview? review,
  }) => TenantVisitDetailsContent(
    visit: visit ?? this.visit,
    propertyId: propertyId ?? this.propertyId,
    location: location ?? this.location,
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    bedrooms: bedrooms ?? this.bedrooms,
    note: note ?? this.note,
    maskedPhone: maskedPhone ?? this.maskedPhone,
    ownerVerified: ownerVerified ?? this.ownerVerified,
    review: review ?? this.review,
  );
  @override
  List<Object?> get props => [
    visit,
    propertyId,
    location,
    price,
    pricePeriod,
    bedrooms,
    note,
    maskedPhone,
    ownerVerified,
    review,
  ];
}
