import 'package:equatable/equatable.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class VisitPropertyContent extends Equatable {
  const VisitPropertyContent({
    this.id = '',
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
      id: json['id'] ?? '',
      ownerId: json['owner_id']?.toString() ?? '',
      title: json['title'] ?? '',
      meta: json['meta'] ?? '',
    );
  }

  final String id;
  final String ownerId;
  final String title;
  final String meta;

  Map<String, dynamic> toJson() => {
    'id': id,
    'owner_id': ownerId,
    'title': title,
    'meta': meta,
  };

  VisitPropertyContent copyWith({
    String? id,
    String? ownerId,
    String? title,
    String? meta,
  }) {
    return VisitPropertyContent(
      id: id ?? this.id,
      ownerId: ownerId ?? this.ownerId,
      title: title ?? this.title,
      meta: meta ?? this.meta,
    );
  }

  @override
  List<Object?> get props => [id, ownerId, title, meta];
}
