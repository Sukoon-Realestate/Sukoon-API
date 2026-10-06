import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class ComparisonProperty extends Equatable {
  const ComparisonProperty({
    required this.propertyId,
    this.property = const PropertyDetailsModel.initial(),
    this.error = '',
    this.isCached = false,
  });
  const ComparisonProperty.initial()
    : propertyId = '',
      property = const PropertyDetailsModel.initial(),
      error = '',
      isCached = false;
  factory ComparisonProperty.fromJson(Map<String, dynamic> json) =>
      ComparisonProperty(
        propertyId: json['property_id'] as String? ?? '',
        property: PropertyDetailsModel.fromJson(
          Map<String, dynamic>.from(json['property'] as Map? ?? const {}),
        ),
        error: json['error'] as String? ?? '',
        isCached: json['is_cached'] == true,
      );
  final String propertyId;
  final PropertyDetailsModel property;
  final String error;
  final bool isCached;
  bool get isAvailable => property.id.isNotEmpty && error.isEmpty;
  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'property': property.toJson(),
    'error': error,
    'is_cached': isCached,
  };
  ComparisonProperty copyWith({
    String? propertyId,
    PropertyDetailsModel? property,
    String? error,
    bool? isCached,
  }) => ComparisonProperty(
    propertyId: propertyId ?? this.propertyId,
    property: property ?? this.property,
    error: error ?? this.error,
    isCached: isCached ?? this.isCached,
  );
  @override
  List<Object?> get props => [propertyId, property, error, isCached];
}
