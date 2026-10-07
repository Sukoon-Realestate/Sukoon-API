import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:equatable/equatable.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class VisitPropertyContent extends Equatable {
  const VisitPropertyContent({
    this.id = '',
    this.selection,
    this.hasRentalOffers = false,
    this.ownerId = '',
    required this.title,
    required this.meta,
  });

  factory VisitPropertyContent.initial() =>
      const VisitPropertyContent(title: '', meta: '');

  factory VisitPropertyContent.fromPropertyDetails(
    TenantPropertyDetailsContent property,
  ) {
    return VisitPropertyContent(
      id: property.id,
      selection: property.selection,
      hasRentalOffers: property.hasRentalOffers,
      ownerId: property.ownerId,
      title: property.shortTitle,
      meta: [
        '${property.price} ${property.pricePeriodLabel}'.trim(),
        if (property.bedrooms != null)
          '${property.bedrooms} ${LocaleKeys.tenantSearchResultsBeds}',
      ].join(' · '),
    );
  }

  factory VisitPropertyContent.fromJson(Map<String, dynamic> json) {
    return VisitPropertyContent(
      selection: json['selection'] is Map
          ? RentalSelection.fromJson(
              Map<String, dynamic>.from(json['selection']),
            )
          : null,
      hasRentalOffers: json['has_rental_offers'] == true,
      id: json['id'] ?? '',
      ownerId: json['owner_id']?.toString() ?? '',
      title: json['title'] ?? '',
      meta: json['meta'] ?? '',
    );
  }

  final RentalSelection? selection;
  final bool hasRentalOffers;
  final String id;
  final String ownerId;
  final String title;
  final String meta;

  Map<String, dynamic> toJson() => {
    'id': id,
    if (selection != null) 'selection': selection!.toJson(),
    'has_rental_offers': hasRentalOffers,
    'owner_id': ownerId,
    'title': title,
    'meta': meta,
  };

  VisitPropertyContent copyWith({
    RentalSelection? selection,
    bool? hasRentalOffers,
    String? id,
    String? ownerId,
    String? title,
    String? meta,
  }) {
    return VisitPropertyContent(
      selection: selection ?? this.selection,
      hasRentalOffers: hasRentalOffers ?? this.hasRentalOffers,
      id: id ?? this.id,
      ownerId: ownerId ?? this.ownerId,
      title: title ?? this.title,
      meta: meta ?? this.meta,
    );
  }

  @override
  List<Object?> get props => [
    selection,
    hasRentalOffers,
    id,
    ownerId,
    title,
    meta,
  ];
}
