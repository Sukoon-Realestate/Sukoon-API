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
    this.ownerId = '',
  });

  const TenantVisitContent.initial()
    : id = '',
      propertyTitle = '',
      day = '',
      time = '',
      status = TenantVisitStatus.pending,
      statusText = '',
      ownerName = '',
      ownerPhone = '',
      ownerId = '';

  factory TenantVisitContent.fromJson(Map<String, dynamic> json) {
    final String statusText = json['status'] as String? ?? '';
    final Object? ownerValue = json['owner'];
    final Map<String, dynamic> owner = ownerValue is Map
        ? Map<String, dynamic>.from(ownerValue)
        : const {};
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
      ownerName:
          json['owner_name']?.toString() ??
          owner['full_name']?.toString() ??
          owner['name']?.toString() ??
          '',
      ownerPhone:
          json['owner_phone']?.toString() ?? owner['phone']?.toString() ?? '',
      ownerId: json['owner_id']?.toString() ?? owner['id']?.toString() ?? '',
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
  final String ownerId;

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
    'owner_id': ownerId,
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
    String? ownerId,
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
      ownerId: ownerId ?? this.ownerId,
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
    ownerId,
  ];
}
