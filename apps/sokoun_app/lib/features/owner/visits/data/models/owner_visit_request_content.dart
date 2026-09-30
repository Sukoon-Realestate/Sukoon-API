part of '../../imports.dart';

class OwnerVisitRequestContent extends Equatable {
  const OwnerVisitRequestContent({
    required this.id,
    required this.initial,
    required this.name,
    required this.property,
    required this.dateLabel,
    required this.detailDate,
    required this.time,
    required this.memberSince,
    required this.tenantNote,
    required this.phone,
    required this.status,
    required this.isVerified,
    this.propertyId = '',
    this.tenantId = '',
  });

  factory OwnerVisitRequestContent.initial() => const OwnerVisitRequestContent(
    id: '',
    initial: '',
    name: '',
    property: '',
    dateLabel: '',
    detailDate: '',
    time: '',
    memberSince: '',
    tenantNote: '',
    phone: '',
    status: OwnerVisitRequestStatus.pending,
    isVerified: false,
    propertyId: '',
    tenantId: '',
  );

  factory OwnerVisitRequestContent.fromJson(Map<String, dynamic> json) {
    final Object? tenantValue = json['tenant'] ?? json['user'];
    final Map<String, dynamic> tenant = tenantValue is Map
        ? tenantValue.cast<String, dynamic>()
        : const {};
    final Object? propertyValue = json['property'];
    final Map<String, dynamic> property = propertyValue is Map
        ? propertyValue.cast<String, dynamic>()
        : const {};
    final String name =
        json['tenant_name'] ??
        json['name'] ??
        tenant['full_name'] ??
        tenant['name'] ??
        '';
    final String visitDate =
        json['visit_date'] ?? json['date'] ?? json['detail_date'] ?? '';
    final String visitTime =
        json['time'] ?? json['visit_time'] ?? property['time'] ?? '';

    return OwnerVisitRequestContent(
      id: json['id'] ?? '',
      initial:
          json['initial'] ??
          tenant['initial'] ??
          (name.isEmpty ? '' : name.substring(0, 1)),
      name: name,
      property:
          json['property_title'] ??
          property['title'] ??
          (propertyValue is String ? propertyValue : '') ??
          '',
      dateLabel:
          json['date_label'] ??
          [visitDate, visitTime].where((value) => value.isNotEmpty).join(' · '),
      detailDate: visitDate,
      time: visitTime,
      memberSince: json['member_since'] ?? tenant['member_since'] ?? '',
      tenantNote: json['tenant_note'] ?? json['note'] ?? '',
      phone: json['phone'] ?? tenant['phone'] ?? '',
      status: OwnerVisitRequestStatusExtension.fromName(json['status']),
      isVerified: json['is_verified'] ?? tenant['is_verified'] ?? false,
      propertyId:
          property['id'] as String? ?? json['property_id'] as String? ?? '',
      tenantId: tenant['id']?.toString() ?? json['tenant_id']?.toString() ?? '',
    );
  }

  static List<OwnerVisitRequestContent> listFromResponse(dynamic json) {
    final dynamic rawItems = json is Map<String, dynamic>
        ? json['results'] ?? json['items'] ?? json['data'] ?? const []
        : json;
    return (rawItems as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(OwnerVisitRequestContent.fromJson)
        .toList(growable: false);
  }

  final String id;
  final String initial;
  final String name;
  final String property;
  final String dateLabel;
  final String detailDate;
  final String time;
  final String memberSince;
  final String tenantNote;
  final String phone;
  final OwnerVisitRequestStatus status;
  final bool isVerified;
  final String propertyId;
  final String tenantId;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'initial': initial,
      'name': name,
      'property': property,
      'date_label': dateLabel,
      'detail_date': detailDate,
      'time': time,
      'member_since': memberSince,
      'tenant_note': tenantNote,
      'phone': phone,
      'status': status.name,
      'is_verified': isVerified,
      'property_id': propertyId,
      'tenant_id': tenantId,
    };
  }

  OwnerVisitRequestContent copyWith({
    String? id,
    String? initial,
    String? name,
    String? property,
    String? dateLabel,
    String? detailDate,
    String? time,
    String? memberSince,
    String? tenantNote,
    String? phone,
    OwnerVisitRequestStatus? status,
    bool? isVerified,
    String? propertyId,
    String? tenantId,
  }) {
    return OwnerVisitRequestContent(
      id: id ?? this.id,
      initial: initial ?? this.initial,
      name: name ?? this.name,
      property: property ?? this.property,
      dateLabel: dateLabel ?? this.dateLabel,
      detailDate: detailDate ?? this.detailDate,
      time: time ?? this.time,
      memberSince: memberSince ?? this.memberSince,
      tenantNote: tenantNote ?? this.tenantNote,
      phone: phone ?? this.phone,
      status: status ?? this.status,
      isVerified: isVerified ?? this.isVerified,
      propertyId: propertyId ?? this.propertyId,
      tenantId: tenantId ?? this.tenantId,
    );
  }

  @override
  List<Object?> get props => [
    id,
    initial,
    name,
    property,
    dateLabel,
    detailDate,
    time,
    memberSince,
    tenantNote,
    phone,
    status,
    isVerified,
    propertyId,
    tenantId,
  ];
}
