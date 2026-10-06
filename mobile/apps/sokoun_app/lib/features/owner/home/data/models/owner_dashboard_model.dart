import 'package:equatable/equatable.dart';

class OwnerDashboardModel extends Equatable {
  const OwnerDashboardModel({
    required this.owner,
    required this.visitsThisWeek,
    required this.activeProperties,
    required this.overallRating,
    required this.pendingRequests,
    required this.pendingVisits,
  });

  const OwnerDashboardModel.initial()
    : owner = const OwnerDashboardOwnerModel.initial(),
      visitsThisWeek = 0,
      activeProperties = 0,
      overallRating = 0,
      pendingRequests = 0,
      pendingVisits = const [];

  factory OwnerDashboardModel.fromJson(Map<String, dynamic> json) {
    final Object? ownerJson = json['owner'];
    return OwnerDashboardModel(
      owner: ownerJson is Map<String, dynamic>
          ? OwnerDashboardOwnerModel.fromJson(ownerJson)
          : const OwnerDashboardOwnerModel.initial(),
      visitsThisWeek: (json['visits_this_week'] as num?)?.toInt() ?? 0,
      activeProperties: (json['active_properties'] as num?)?.toInt() ?? 0,
      overallRating: (json['overall_rating'] as num?)?.toDouble() ?? 0,
      pendingRequests: (json['pending_requests'] as num?)?.toInt() ?? 0,
      pendingVisits:
          (json['pending_visits'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerDashboardPendingVisitModel.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final OwnerDashboardOwnerModel owner;
  final int visitsThisWeek;
  final int activeProperties;
  final double overallRating;
  final int pendingRequests;
  final List<OwnerDashboardPendingVisitModel> pendingVisits;

  Map<String, dynamic> toJson() => {
    'owner': owner.toJson(),
    'visits_this_week': visitsThisWeek,
    'active_properties': activeProperties,
    'overall_rating': overallRating,
    'pending_requests': pendingRequests,
    'pending_visits': pendingVisits
        .map((visit) => visit.toJson())
        .toList(growable: false),
  };

  OwnerDashboardModel copyWith({
    OwnerDashboardOwnerModel? owner,
    int? visitsThisWeek,
    int? activeProperties,
    double? overallRating,
    int? pendingRequests,
    List<OwnerDashboardPendingVisitModel>? pendingVisits,
  }) {
    return OwnerDashboardModel(
      owner: owner ?? this.owner,
      visitsThisWeek: visitsThisWeek ?? this.visitsThisWeek,
      activeProperties: activeProperties ?? this.activeProperties,
      overallRating: overallRating ?? this.overallRating,
      pendingRequests: pendingRequests ?? this.pendingRequests,
      pendingVisits: pendingVisits ?? this.pendingVisits,
    );
  }

  @override
  List<Object?> get props => [
    owner,
    visitsThisWeek,
    activeProperties,
    overallRating,
    pendingRequests,
    pendingVisits,
  ];
}

class OwnerDashboardOwnerModel extends Equatable {
  const OwnerDashboardOwnerModel({
    required this.name,
    required this.avatar,
    required this.isVerified,
  });

  const OwnerDashboardOwnerModel.initial()
    : name = '',
      avatar = null,
      isVerified = false;

  factory OwnerDashboardOwnerModel.fromJson(Map<String, dynamic> json) {
    return OwnerDashboardOwnerModel(
      name: json['name'] as String? ?? '',
      avatar: _nullableString(json['avatar']),
      isVerified: json['is_verified'] as bool? ?? false,
    );
  }

  final String name;
  final String? avatar;
  final bool isVerified;

  Map<String, dynamic> toJson() => {
    'name': name,
    'avatar': avatar,
    'is_verified': isVerified,
  };

  OwnerDashboardOwnerModel copyWith({
    String? name,
    String? avatar,
    bool clearAvatar = false,
    bool? isVerified,
  }) {
    return OwnerDashboardOwnerModel(
      name: name ?? this.name,
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      isVerified: isVerified ?? this.isVerified,
    );
  }

  @override
  List<Object?> get props => [name, avatar, isVerified];
}

class OwnerDashboardPendingVisitModel extends Equatable {
  const OwnerDashboardPendingVisitModel({
    required this.id,
    required this.tenantName,
    required this.tenantAvatar,
    required this.propertyTitle,
    required this.propertyDistrict,
    required this.scheduledAt,
  });

  const OwnerDashboardPendingVisitModel.initial()
    : id = '',
      tenantName = '',
      tenantAvatar = null,
      propertyTitle = '',
      propertyDistrict = '',
      scheduledAt = '';

  factory OwnerDashboardPendingVisitModel.fromJson(Map<String, dynamic> json) {
    return OwnerDashboardPendingVisitModel(
      id: json['id'] as String? ?? '',
      tenantName: json['tenant_name'] as String? ?? '',
      tenantAvatar: _nullableString(json['tenant_avatar']),
      propertyTitle: json['property_title'] as String? ?? '',
      propertyDistrict: json['property_district'] as String? ?? '',
      scheduledAt: json['scheduled_at'] as String? ?? '',
    );
  }

  final String id;
  final String tenantName;
  final String? tenantAvatar;
  final String propertyTitle;
  final String propertyDistrict;
  final String scheduledAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant_name': tenantName,
    'tenant_avatar': tenantAvatar,
    'property_title': propertyTitle,
    'property_district': propertyDistrict,
    'scheduled_at': scheduledAt,
  };

  OwnerDashboardPendingVisitModel copyWith({
    String? id,
    String? tenantName,
    String? tenantAvatar,
    bool clearTenantAvatar = false,
    String? propertyTitle,
    String? propertyDistrict,
    String? scheduledAt,
  }) {
    return OwnerDashboardPendingVisitModel(
      id: id ?? this.id,
      tenantName: tenantName ?? this.tenantName,
      tenantAvatar: clearTenantAvatar
          ? null
          : tenantAvatar ?? this.tenantAvatar,
      propertyTitle: propertyTitle ?? this.propertyTitle,
      propertyDistrict: propertyDistrict ?? this.propertyDistrict,
      scheduledAt: scheduledAt ?? this.scheduledAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    tenantName,
    tenantAvatar,
    propertyTitle,
    propertyDistrict,
    scheduledAt,
  ];
}

String? _nullableString(Object? value) {
  final String? stringValue = value?.toString().trim();
  return stringValue == null || stringValue.isEmpty ? null : stringValue;
}
