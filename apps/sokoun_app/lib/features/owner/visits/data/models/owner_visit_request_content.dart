import 'package:sokoun_app/features/shared/contact/data/phone_disclosure.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import '../enums/owner_visit_request_state.dart';
import '../owner_visit_json.dart';
import 'owner_visit_request_details_content.dart';
import 'package:equatable/equatable.dart';

class OwnerVisitRequestContent extends Equatable {
  const OwnerVisitRequestContent({
    this.rentalSelection,
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
    this.isPhoneRevealed,
    this.propertyId = '',
    this.tenantId = '',
    this.actions,
    this.avatar = '',
    this.subtitle = '',
    this.statusLabel = '',
    this.verificationWarning = '',
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
      rentalSelection: RentalSelection.fromRecord(json),
      id: json['id'] ?? '',
      initial:
          json['initial'] ??
          tenant['initial'] ??
          (name.isEmpty ? '' : name.substring(0, 1)),
      name: name,
      property:
          json['property_title'] ??
          (property.isNotEmpty
              ? [property['title'], property['district']]
                    .whereType<String>()
                    .where((value) => value.trim().isNotEmpty)
                    .join(' · ')
              : null) ??
          (propertyValue is String ? propertyValue : '') ??
          '',
      dateLabel:
          json['schedule_label'] ??
          json['date_label'] ??
          [visitDate, visitTime].where((value) => value.isNotEmpty).join(' · '),
      detailDate: visitDate,
      time: visitTime,
      memberSince: json['member_since'] ?? tenant['member_since'] ?? '',
      tenantNote: json['tenant_note'] ?? json['note'] ?? '',
      phone: ownerVisitString(
        tenant['phone_number'] ?? json['phone'] ?? tenant['phone'],
      ),
      isPhoneRevealed:
          (tenant['is_phone_revealed'] ?? json['is_phone_revealed']) as bool?,
      status: OwnerVisitRequestStatusExtension.fromName(json['status']),
      isVerified:
          json['is_verified_tenant'] ??
          json['is_verified'] ??
          tenant['is_verified'] ??
          false,
      avatar: ownerVisitString(tenant['avatar'] ?? json['avatar']),
      subtitle: ownerVisitString(json['subtitle']),
      statusLabel: ownerVisitString(json['status_label']),
      verificationWarning: ownerVisitString(json['verification_warning']),
      propertyId:
          property['id'] as String? ?? json['property_id'] as String? ?? '',
      tenantId: tenant['id']?.toString() ?? json['tenant_id']?.toString() ?? '',
      actions: json['actions'] is Map
          ? OwnerVisitRequestActionsContent.fromJson(
              ownerVisitJsonMap(json['actions']),
            )
          : null,
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

  final RentalSelection? rentalSelection;
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
  final bool? isPhoneRevealed;
  String get revealedPhone => PhoneDisclosure.revealedPhone(
    phoneNumber: phone,
    isPhoneRevealed: isPhoneRevealed,
    hasAcceptedVisit: status.isAccepted || status.isCompleted,
  );
  final OwnerVisitRequestStatus status;
  final bool isVerified;
  final String propertyId;
  final String tenantId;
  final OwnerVisitRequestActionsContent? actions;
  final String avatar;
  final String subtitle;
  final String statusLabel;
  final String verificationWarning;
  bool get canAccept => status.canDecide && (actions?.canAccept ?? true);
  bool get canReject => status.canDecide && (actions?.canReject ?? true);
  bool get canChat => tenantId.isNotEmpty && (actions?.canChat ?? true);

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      if (rentalSelection != null) ...{
        'offer_id': rentalSelection!.offerId,
        'offer_snapshot': rentalSelection!.toJson(),
      },
      'initial': initial,
      'name': name,
      'property': property,
      'date_label': dateLabel,
      'detail_date': detailDate,
      'time': time,
      'member_since': memberSince,
      'tenant_note': tenantNote,
      'phone': phone,
      if (isPhoneRevealed != null) 'is_phone_revealed': isPhoneRevealed,
      'status': status.name,
      'is_verified': isVerified,
      'property_id': propertyId,
      'tenant_id': tenantId,
      'avatar': avatar,
      'subtitle': subtitle,
      'status_label': statusLabel,
      'verification_warning': verificationWarning,
      if (actions != null) 'actions': actions!.toJson(),
    };
  }

  OwnerVisitRequestContent copyWith({
    RentalSelection? rentalSelection,
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
    bool? isPhoneRevealed,
    OwnerVisitRequestStatus? status,
    bool? isVerified,
    String? propertyId,
    String? tenantId,
    OwnerVisitRequestActionsContent? actions,
    String? avatar,
    String? subtitle,
    String? statusLabel,
    String? verificationWarning,
  }) {
    return OwnerVisitRequestContent(
      rentalSelection: rentalSelection ?? this.rentalSelection,
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
      isPhoneRevealed: isPhoneRevealed ?? this.isPhoneRevealed,
      status: status ?? this.status,
      isVerified: isVerified ?? this.isVerified,
      propertyId: propertyId ?? this.propertyId,
      tenantId: tenantId ?? this.tenantId,
      actions: actions ?? this.actions,
      avatar: avatar ?? this.avatar,
      subtitle: subtitle ?? this.subtitle,
      statusLabel: statusLabel ?? this.statusLabel,
      verificationWarning: verificationWarning ?? this.verificationWarning,
    );
  }

  @override
  List<Object?> get props => [
    rentalSelection,
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
    isPhoneRevealed,
    status,
    isVerified,
    propertyId,
    tenantId,
    actions,
    avatar,
    subtitle,
    statusLabel,
    verificationWarning,
  ];
}
