part of '../../imports.dart';

class TenantVisitContent extends Equatable {
  const TenantVisitContent({
    required this.id,
    required this.propertyTitle,
    required this.day,
    required this.time,
    required this.status,
    required this.statusText,
    this.ownerName = '',
    this.ownerPhone = '',
  });

  const TenantVisitContent.initial()
    : id = '',
      propertyTitle = '',
      day = '',
      time = '',
      status = TenantVisitStatus.pending,
      statusText = '',
      ownerName = '',
      ownerPhone = '';

  factory TenantVisitContent.fromJson(Map<String, dynamic> json) {
    final String statusText = json['status'] as String? ?? '';
    return TenantVisitContent(
      id: json['id'] as String? ?? '',
      propertyTitle:
          json['title'] as String? ?? json['property_title'] as String? ?? '',
      day:
          json['day'] as String? ??
          json['detail_date'] as String? ??
          json['date_label'] as String? ??
          '',
      time: json['time'] as String? ?? '',
      status: TenantVisitStatusX.fromApiValue(statusText),
      statusText: statusText,
      ownerName: json['owner_name'] as String? ?? '',
      ownerPhone: json['owner_phone'] as String? ?? '',
    );
  }

  final String id;
  final String propertyTitle;
  final String day;
  final String time;
  final TenantVisitStatus status;
  final String statusText;
  final String ownerName;
  final String ownerPhone;

  String get dateLabel =>
      [day, time].where((value) => value.trim().isNotEmpty).join(' · ');

  String get detailDate => day;

  String get resolvedStatusText =>
      statusText.trim().isEmpty ? status.label : statusText;

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': propertyTitle,
    'day': day,
    'time': time,
    'status': statusText.isEmpty ? status.name : statusText,
    'owner_name': ownerName,
    'owner_phone': ownerPhone,
  };

  TenantVisitContent copyWith({
    String? id,
    String? propertyTitle,
    String? day,
    String? time,
    TenantVisitStatus? status,
    String? statusText,
    String? ownerName,
    String? ownerPhone,
  }) {
    return TenantVisitContent(
      id: id ?? this.id,
      propertyTitle: propertyTitle ?? this.propertyTitle,
      day: day ?? this.day,
      time: time ?? this.time,
      status: status ?? this.status,
      statusText: statusText ?? this.statusText,
      ownerName: ownerName ?? this.ownerName,
      ownerPhone: ownerPhone ?? this.ownerPhone,
    );
  }

  @override
  List<Object?> get props => [
    id,
    propertyTitle,
    day,
    time,
    status,
    statusText,
    ownerName,
    ownerPhone,
  ];
}
