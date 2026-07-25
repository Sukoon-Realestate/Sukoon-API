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
    return OwnerVisitRequestContent(
      id: json['id'] ?? '',
      initial: json['initial'] ?? '',
      name: json['name'] ?? '',
      property: json['property'] ?? '',
      dateLabel: json['date_label'] ?? '',
      detailDate: json['detail_date'] ?? '',
      time: json['time'] ?? '',
      memberSince: json['member_since'] ?? '',
      tenantNote: json['tenant_note'] ?? '',
      phone: json['phone'] ?? '',
      status: OwnerVisitRequestStatus.values.firstWhere(
        (status) => status.name == json['status'],
        orElse: () => OwnerVisitRequestStatus.pending,
      ),
      isVerified: json['is_verified'] ?? false,
    );
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

abstract final class OwnerVisitRequestsContent {
  static List<OwnerVisitRequestContent> get requests => [
    OwnerVisitRequestContent(
      id: 'sara-nasr-city',
      initial: LocaleKeys.ownerVisitTenantSaraInitial,
      name: LocaleKeys.ownerVisitTenantSara,
      property: LocaleKeys.ownerVisitPropertyNasrCity,
      dateLabel: LocaleKeys.ownerVisitDateSaturdayAtThree,
      detailDate: LocaleKeys.ownerVisitDateSaturday,
      time: LocaleKeys.ownerVisitTimeThreePm,
      memberSince: LocaleKeys.ownerVisitVerifiedMemberSince,
      tenantNote: LocaleKeys.ownerVisitTenantNote,
      phone: LocaleKeys.ownerVisitTenantPhone,
      status: OwnerVisitRequestStatus.newRequest,
      isVerified: true,
    ),
    OwnerVisitRequestContent(
      id: 'mohamed-jeddah',
      initial: LocaleKeys.ownerVisitTenantMohamedInitial,
      name: LocaleKeys.ownerVisitTenantMohamed,
      property: LocaleKeys.ownerVisitPropertyJeddahStudio,
      dateLabel: LocaleKeys.ownerVisitDateSundayAtTwo,
      detailDate: LocaleKeys.ownerVisitDateSunday,
      time: LocaleKeys.ownerVisitTimeTwoPm,
      memberSince: LocaleKeys.ownerVisitVerifiedMemberSince,
      tenantNote: LocaleKeys.ownerVisitTenantNote,
      phone: LocaleKeys.ownerVisitTenantPhone,
      status: OwnerVisitRequestStatus.accepted,
      isVerified: true,
    ),
    OwnerVisitRequestContent(
      id: 'khaled-dammam',
      initial: LocaleKeys.ownerVisitTenantKhaledInitial,
      name: LocaleKeys.ownerVisitTenantKhaled,
      property: LocaleKeys.ownerVisitPropertyDammamRoom,
      dateLabel: LocaleKeys.ownerVisitDateMondayAtEleven,
      detailDate: LocaleKeys.ownerVisitDateMonday,
      time: LocaleKeys.ownerVisitTimeElevenAm,
      memberSince: LocaleKeys.ownerVisitMemberSince,
      tenantNote: LocaleKeys.ownerVisitTenantNote,
      phone: LocaleKeys.ownerVisitTenantPhone,
      status: OwnerVisitRequestStatus.newRequest,
      isVerified: false,
    ),
  ];
}
