import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class ListingAiFacts extends Equatable {
  const ListingAiFacts({
    this.title = '',
    this.description = '',
    this.propertyType = '',
    this.price = '',
    this.pricePeriod = '',
    this.deposit = '',
    this.bedrooms = 0,
    this.bathrooms = 0,
    this.space = '',
    this.governorate = '',
    this.district = '',
    this.amenities = const [],
  });
  const ListingAiFacts.initial() : this();
  factory ListingAiFacts.fromJson(Map<String, dynamic> json) => ListingAiFacts(
    title: premiumString(json['title']),
    description: premiumString(json['description']),
    propertyType: premiumString(json['property_type']),
    price: premiumString(json['price']),
    pricePeriod: premiumString(json['price_period']),
    deposit: premiumString(json['deposit']),
    bedrooms: premiumInt(json['bedrooms']) ?? 0,
    bathrooms: premiumInt(json['bathrooms']) ?? 0,
    space: premiumString(json['space']),
    governorate: premiumString(json['governorate']),
    district: premiumString(json['district']),
    amenities:
        (json['amenities'] is List ? json['amenities'] as List : const [])
            .whereType<String>()
            .toList(growable: false),
  );
  factory ListingAiFacts.fromForm(OwnerAddPropertyFormState form) =>
      ListingAiFacts(
        title: form.title,
        description: form.description,
        propertyType: form.propertyTypeApiValue,
        price: form.monthlyPrice,
        pricePeriod: form.rentalUnitApiValue,
        deposit: form.deposit,
        bedrooms: int.tryParse(form.bedrooms) ?? 0,
        bathrooms: int.tryParse(form.bathrooms) ?? 0,
        space: form.space,
        governorate: form.governorate,
        district: form.district,
        amenities: form.amenityApiValues.toList(growable: false),
      );
  factory ListingAiFacts.fromProperty(OwnerPropertyContent property) =>
      ListingAiFacts(
        title: property.title,
        description: property.description,
        price: property.monthlyPrice > 0
            ? property.monthlyPrice.toString()
            : '',
        pricePeriod: property.pricePeriod,
        bedrooms: property.bedrooms,
        space: property.area > 0 ? property.area.toString() : '',
      );

  final String title;
  final String description;
  final String propertyType;
  final String price;
  final String pricePeriod;
  final String deposit;
  final int bedrooms;
  final int bathrooms;
  final String space;
  final String governorate;
  final String district;
  final List<String> amenities;

  Map<String, dynamic> toJson() => {
    'title': title,
    'description': description,
    'property_type': propertyType,
    'price': price,
    'price_period': pricePeriod,
    'deposit': deposit,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'space': space,
    'governorate': governorate,
    'district': district,
    'amenities': amenities,
  };
  ListingAiFacts copyWith({
    String? title,
    String? description,
    String? propertyType,
    String? price,
    String? pricePeriod,
    String? deposit,
    int? bedrooms,
    int? bathrooms,
    String? space,
    String? governorate,
    String? district,
    List<String>? amenities,
  }) => ListingAiFacts(
    title: title ?? this.title,
    description: description ?? this.description,
    propertyType: propertyType ?? this.propertyType,
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    deposit: deposit ?? this.deposit,
    bedrooms: bedrooms ?? this.bedrooms,
    bathrooms: bathrooms ?? this.bathrooms,
    space: space ?? this.space,
    governorate: governorate ?? this.governorate,
    district: district ?? this.district,
    amenities: amenities ?? this.amenities,
  );
  @override
  List<Object?> get props => [
    title,
    description,
    propertyType,
    price,
    pricePeriod,
    deposit,
    bedrooms,
    bathrooms,
    space,
    governorate,
    district,
    amenities,
  ];
}
