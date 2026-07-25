part of '../../imports.dart';

class VisitPropertyContent {
  const VisitPropertyContent({required this.title, required this.meta});

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
      title: property.shortTitle,
      meta: LocaleKeys.tenantVisitBookingPropertyMeta,
    );
  }

  factory VisitPropertyContent.fromJson(Map<String, dynamic> json) {
    return VisitPropertyContent(
      title: json['title'] ?? '',
      meta: json['meta'] ?? '',
    );
  }

  final String title;
  final String meta;

  Map<String, dynamic> toJson() => {'title': title, 'meta': meta};

  VisitPropertyContent copyWith({String? title, String? meta}) {
    return VisitPropertyContent(
      title: title ?? this.title,
      meta: meta ?? this.meta,
    );
  }
}
