part of '../../imports.dart';

class OwnerVisitRequestContent {
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
  );

  factory OwnerVisitRequestContent.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> tenant =
        (json['tenant'] as Map?)?.cast<String, dynamic>() ??
        (json['user'] as Map?)?.cast<String, dynamic>() ??
        const {};
    final Map<String, dynamic> property =
        (json['property'] as Map?)?.cast<String, dynamic>() ?? const {};
    final String name =
        json['tenant_name'] ??
        json['name'] ??
        tenant['full_name'] ??
        tenant['name'] ??
        '';
    final String visitDate =
        json['visit_date'] ?? json['date'] ?? json['detail_date'] ?? '';
    final String visitTime =
        json['visit_time'] ?? json['time'] ?? property['time'] ?? '';

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
          (json['property'] is String ? json['property'] : '') ??
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
    );
  }
}
