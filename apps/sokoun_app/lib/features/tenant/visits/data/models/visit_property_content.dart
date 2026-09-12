part of '../../imports.dart';

class VisitPropertyContent extends Equatable {
  const VisitPropertyContent({
    this.id = '',
    required this.title,
    required this.meta,
  });

  factory VisitPropertyContent.initial() =>
      const VisitPropertyContent(title: '', meta: '');

  factory VisitPropertyContent.prototype() {
    return VisitPropertyContent(
      title: LocaleKeys.tenantVisitBookingPropertyTitle,
      meta: LocaleKeys.tenantVisitBookingPropertyMeta,
    );
  }

  factory VisitPropertyContent.fromPropertyDetails(
    TenantPropertyDetailsContent property,
  ) {
    return VisitPropertyContent(
      id: property.id,
      title: property.shortTitle,
      meta: LocaleKeys.tenantVisitBookingPropertyMeta,
    );
  }

  factory VisitPropertyContent.fromJson(Map<String, dynamic> json) {
    return VisitPropertyContent(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      meta: json['meta'] ?? '',
    );
  }

  final String id;
  final String title;
  final String meta;

  Map<String, dynamic> toJson() => {'id': id, 'title': title, 'meta': meta};

  VisitPropertyContent copyWith({String? id, String? title, String? meta}) {
    return VisitPropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
      meta: meta ?? this.meta,
    );
  }

  @override
  List<Object?> get props => [id, title, meta];
}
