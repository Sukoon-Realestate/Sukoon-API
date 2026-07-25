part of '../../imports.dart';

class TenantVisitContent {
  const TenantVisitContent({
    required this.id,
    required this.propertyTitle,
    required this.ownerName,
    required this.dateLabel,
    required this.status,
    required this.detailDate,
    required this.time,
    required this.ownerPhone,
  });

  factory TenantVisitContent.initial() => const TenantVisitContent(
    id: '',
    propertyTitle: '',
    ownerName: '',
    dateLabel: '',
    status: TenantVisitStatus.pending,
    detailDate: '',
    time: '',
    ownerPhone: '',
  );

  factory TenantVisitContent.fromJson(Map<String, dynamic> json) {
    return TenantVisitContent(
      id: json['id'] ?? '',
      propertyTitle: json['property_title'] ?? '',
      ownerName: json['owner_name'] ?? '',
      dateLabel: json['date_label'] ?? '',
      status: TenantVisitStatus.values.firstWhere(
        (status) => status.name == json['status'],
        orElse: () => TenantVisitStatus.pending,
      ),
      detailDate: json['detail_date'] ?? '',
      time: json['time'] ?? '',
      ownerPhone: json['owner_phone'] ?? '',
    );
  }

  final String id;
  final String propertyTitle;
  final String ownerName;
  final String dateLabel;
  final TenantVisitStatus status;
  final String detailDate;
  final String time;
  final String ownerPhone;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'property_title': propertyTitle,
      'owner_name': ownerName,
      'date_label': dateLabel,
      'status': status.name,
      'detail_date': detailDate,
      'time': time,
      'owner_phone': ownerPhone,
    };
  }

  TenantVisitContent copyWith({
    String? id,
    String? propertyTitle,
    String? ownerName,
    String? dateLabel,
    TenantVisitStatus? status,
    String? detailDate,
    String? time,
    String? ownerPhone,
  }) {
    return TenantVisitContent(
      id: id ?? this.id,
      propertyTitle: propertyTitle ?? this.propertyTitle,
      ownerName: ownerName ?? this.ownerName,
      dateLabel: dateLabel ?? this.dateLabel,
      status: status ?? this.status,
      detailDate: detailDate ?? this.detailDate,
      time: time ?? this.time,
      ownerPhone: ownerPhone ?? this.ownerPhone,
    );
  }
}
