import '../enums/owner_visit_request_state.dart';
import '../owner_visit_json.dart';
import 'owner_visit_request_content.dart';
import 'package:equatable/equatable.dart';

class OwnerVisitRequestDetailsContent extends Equatable {
  const OwnerVisitRequestDetailsContent({
    required this.id,
    required this.tenant,
    required this.property,
    required this.visitDate,
    required this.visitTime,
    required this.dayLabel,
    required this.timeLabel,
    required this.note,
    required this.status,
    required this.statusLabel,
    required this.actions,
    required this.createdAt,
  });

  const OwnerVisitRequestDetailsContent.initial()
    : id = '',
      tenant = const OwnerVisitRequestTenantContent.initial(),
      property = const OwnerVisitRequestPropertyContent.initial(),
      visitDate = '',
      visitTime = '',
      dayLabel = '',
      timeLabel = '',
      note = '',
      status = OwnerVisitRequestStatus.pending,
      statusLabel = '',
      actions = const OwnerVisitRequestActionsContent.initial(),
      createdAt = '';

  factory OwnerVisitRequestDetailsContent.fromJson(Map<String, dynamic> json) {
    return OwnerVisitRequestDetailsContent(
      id: ownerVisitString(json['id']),
      tenant: OwnerVisitRequestTenantContent.fromJson(
        ownerVisitJsonMap(json['tenant']),
      ),
      property: OwnerVisitRequestPropertyContent.fromJson(
        ownerVisitJsonMap(json['property']),
      ),
      visitDate: ownerVisitString(json['visit_date']),
      visitTime: ownerVisitString(json['visit_time']),
      dayLabel: ownerVisitString(json['day_label']),
      timeLabel: ownerVisitString(json['time_label']),
      note: ownerVisitString(json['note']),
      status: OwnerVisitRequestStatusExtension.fromName(
        ownerVisitString(json['status']),
      ),
      statusLabel: ownerVisitString(json['status_label']),
      actions: OwnerVisitRequestActionsContent.fromJson(
        ownerVisitJsonMap(json['actions']),
      ),
      createdAt: ownerVisitString(json['created_at']),
    );
  }

  final String id;
  final OwnerVisitRequestTenantContent tenant;
  final OwnerVisitRequestPropertyContent property;
  final String visitDate;
  final String visitTime;
  final String dayLabel;
  final String timeLabel;
  final String note;
  final OwnerVisitRequestStatus status;
  final String statusLabel;
  final OwnerVisitRequestActionsContent actions;
  final String createdAt;

  String get displayProperty {
    if (property.displayName.isNotEmpty) return property.displayName;
    return [
      property.title,
      property.district,
    ].where((value) => value.isNotEmpty).join(' – ');
  }

  String get displayDate => dayLabel.isNotEmpty ? dayLabel : visitDate;

  String get displayTime => timeLabel.isNotEmpty ? timeLabel : visitTime;

  String get displayStatus =>
      statusLabel.isNotEmpty ? statusLabel : status.label;

  OwnerVisitRequestContent toRequestContent() {
    final String tenantName = tenant.name.trim();
    return OwnerVisitRequestContent(
      id: id,
      initial: tenantName.isEmpty ? '' : tenantName.substring(0, 1),
      name: tenantName,
      property: displayProperty,
      dateLabel: [
        displayDate,
        displayTime,
      ].where((value) => value.isNotEmpty).join(' · '),
      detailDate: displayDate,
      time: displayTime,
      memberSince: tenant.membershipLabel,
      tenantNote: note,
      phone: tenant.displayPhone,
      status: status,
      isVerified: tenant.isVerified,
      propertyId: property.id,
      tenantId: tenant.id,
      avatar: tenant.avatar,
      statusLabel: statusLabel,
      actions: actions,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant': tenant.toJson(),
    'property': property.toJson(),
    'visit_date': visitDate,
    'visit_time': visitTime,
    'day_label': dayLabel,
    'time_label': timeLabel,
    'note': note,
    'status': status.name,
    'status_label': statusLabel,
    'actions': actions.toJson(),
    'created_at': createdAt,
  };

  OwnerVisitRequestDetailsContent copyWith({
    String? id,
    OwnerVisitRequestTenantContent? tenant,
    OwnerVisitRequestPropertyContent? property,
    String? visitDate,
    String? visitTime,
    String? dayLabel,
    String? timeLabel,
    String? note,
    OwnerVisitRequestStatus? status,
    String? statusLabel,
    OwnerVisitRequestActionsContent? actions,
    String? createdAt,
  }) {
    return OwnerVisitRequestDetailsContent(
      id: id ?? this.id,
      tenant: tenant ?? this.tenant,
      property: property ?? this.property,
      visitDate: visitDate ?? this.visitDate,
      visitTime: visitTime ?? this.visitTime,
      dayLabel: dayLabel ?? this.dayLabel,
      timeLabel: timeLabel ?? this.timeLabel,
      note: note ?? this.note,
      status: status ?? this.status,
      statusLabel: statusLabel ?? this.statusLabel,
      actions: actions ?? this.actions,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    tenant,
    property,
    visitDate,
    visitTime,
    dayLabel,
    timeLabel,
    note,
    status,
    statusLabel,
    actions,
    createdAt,
  ];
}

class OwnerVisitRequestTenantContent extends Equatable {
  const OwnerVisitRequestTenantContent({
    required this.id,
    required this.name,
    required this.avatar,
    required this.isVerified,
    required this.memberSinceYear,
    required this.membershipLabel,
    required this.phoneNumber,
    required this.maskedPhoneNumber,
    required this.isPhoneRevealed,
    required this.phoneNotice,
  });

  const OwnerVisitRequestTenantContent.initial()
    : id = '',
      name = '',
      avatar = '',
      isVerified = false,
      memberSinceYear = 0,
      membershipLabel = '',
      phoneNumber = '',
      maskedPhoneNumber = '',
      isPhoneRevealed = false,
      phoneNotice = '';

  factory OwnerVisitRequestTenantContent.fromJson(Map<String, dynamic> json) {
    return OwnerVisitRequestTenantContent(
      id: ownerVisitString(json['id']),
      name: ownerVisitString(json['name'] ?? json['full_name']),
      avatar: ownerVisitString(json['avatar']),
      isVerified: json['is_verified'] ?? false,
      memberSinceYear: (json['member_since_year'] as num?)?.toInt() ?? 0,
      membershipLabel: ownerVisitString(json['membership_label']),
      phoneNumber: ownerVisitString(json['phone_number']),
      maskedPhoneNumber: ownerVisitString(json['masked_phone_number']),
      isPhoneRevealed: json['is_phone_revealed'] ?? false,
      phoneNotice: ownerVisitString(json['phone_notice']),
    );
  }

  final String id;
  final String name;
  final String avatar;
  final bool isVerified;
  final int memberSinceYear;
  final String membershipLabel;
  final String phoneNumber;
  final String maskedPhoneNumber;
  final bool isPhoneRevealed;
  final String phoneNotice;

  String get displayPhone {
    if (isPhoneRevealed && phoneNumber.isNotEmpty) return phoneNumber;
    return maskedPhoneNumber;
  }

  String get displayPhoneNotice {
    if (phoneNotice.isNotEmpty) return phoneNotice;
    return displayPhone;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'avatar': avatar,
    'is_verified': isVerified,
    'member_since_year': memberSinceYear,
    'membership_label': membershipLabel,
    'phone_number': phoneNumber,
    'masked_phone_number': maskedPhoneNumber,
    'is_phone_revealed': isPhoneRevealed,
    'phone_notice': phoneNotice,
  };

  OwnerVisitRequestTenantContent copyWith({
    String? id,
    String? name,
    String? avatar,
    bool? isVerified,
    int? memberSinceYear,
    String? membershipLabel,
    String? phoneNumber,
    String? maskedPhoneNumber,
    bool? isPhoneRevealed,
    String? phoneNotice,
  }) {
    return OwnerVisitRequestTenantContent(
      id: id ?? this.id,
      name: name ?? this.name,
      avatar: avatar ?? this.avatar,
      isVerified: isVerified ?? this.isVerified,
      memberSinceYear: memberSinceYear ?? this.memberSinceYear,
      membershipLabel: membershipLabel ?? this.membershipLabel,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      maskedPhoneNumber: maskedPhoneNumber ?? this.maskedPhoneNumber,
      isPhoneRevealed: isPhoneRevealed ?? this.isPhoneRevealed,
      phoneNotice: phoneNotice ?? this.phoneNotice,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    avatar,
    isVerified,
    memberSinceYear,
    membershipLabel,
    phoneNumber,
    maskedPhoneNumber,
    isPhoneRevealed,
    phoneNotice,
  ];
}

class OwnerVisitRequestPropertyContent extends Equatable {
  const OwnerVisitRequestPropertyContent({
    required this.id,
    required this.title,
    required this.district,
    required this.displayName,
  });

  const OwnerVisitRequestPropertyContent.initial()
    : id = '',
      title = '',
      district = '',
      displayName = '';

  factory OwnerVisitRequestPropertyContent.fromJson(Map<String, dynamic> json) {
    return OwnerVisitRequestPropertyContent(
      id: ownerVisitString(json['id']),
      title: ownerVisitString(json['title']),
      district: ownerVisitString(json['district']),
      displayName: ownerVisitString(json['display_name']),
    );
  }

  final String id;
  final String title;
  final String district;
  final String displayName;

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'district': district,
    'display_name': displayName,
  };

  OwnerVisitRequestPropertyContent copyWith({
    String? id,
    String? title,
    String? district,
    String? displayName,
  }) {
    return OwnerVisitRequestPropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
      district: district ?? this.district,
      displayName: displayName ?? this.displayName,
    );
  }

  @override
  List<Object?> get props => [id, title, district, displayName];
}

class OwnerVisitRequestActionsContent extends Equatable {
  const OwnerVisitRequestActionsContent({
    required this.canAccept,
    required this.canReject,
    required this.canChat,
  });

  const OwnerVisitRequestActionsContent.initial()
    : canAccept = true,
      canReject = true,
      canChat = false;

  factory OwnerVisitRequestActionsContent.fromJson(Map<String, dynamic> json) {
    return OwnerVisitRequestActionsContent(
      canAccept: json['can_accept'] ?? false,
      canReject: json['can_reject'] ?? false,
      canChat: json['can_chat'] ?? false,
    );
  }

  final bool canAccept;
  final bool canReject;
  final bool canChat;

  Map<String, dynamic> toJson() => {
    'can_accept': canAccept,
    'can_reject': canReject,
    'can_chat': canChat,
  };

  OwnerVisitRequestActionsContent copyWith({
    bool? canAccept,
    bool? canReject,
    bool? canChat,
  }) {
    return OwnerVisitRequestActionsContent(
      canAccept: canAccept ?? this.canAccept,
      canReject: canReject ?? this.canReject,
      canChat: canChat ?? this.canChat,
    );
  }

  @override
  List<Object?> get props => [canAccept, canReject, canChat];
}
